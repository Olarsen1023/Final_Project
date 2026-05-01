"""
Wedding Seating Chart Algorithm

This script assigns wedding guests to tables while respecting:
- Conflicts: Pairs of guests who cannot sit at the same table
- Groups: Groups of guests who must all sit at the same table

Usage:
    python seating_algorithm.py

Input files (in data/ directory):
    - Guest List CSV: List of all guest names, one per line
    - conflicts.csv: Pairs of guests who cannot sit together
    - groups.csv: Groups of guests who must sit together

Output:
    - Prints seating chart to console
    - Exports seating chart to data/seating_chart.csv
"""

import csv
import random
import sys
from collections import defaultdict


# =============================================================================
# CONFIGURATION
# =============================================================================

NUM_TABLES = 9           # Number of tables available
SEATS_PER_TABLE = 8     # Maximum seats per table
GUEST_FILE = 'data/Guest List for Final - Sheet1.csv'  # Guest list input
CONFLICT_FILE = 'data/conflicts.csv'      # Conflict pairs input
GROUP_FILE = 'data/groups.csv'            # Group definitions input
OUTPUT_CSV = 'data/seating_chart.csv'     # Output seating chart


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_guests(filename):
    """
    Load guest list from a CSV file.
    
    Args:
        filename (str): Path to the guest list CSV file
        
    Returns:
        list: List of guest names (strings)
        
    Notes:
        - Empty lines are skipped
        - Each line should contain one guest name
    """
    guests = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows
            if row and row[0].strip():
                guests.append(row[0].strip())
    return guests


def load_conflicts(filename):
    """
    Load conflict pairs from a CSV file.
    
    A conflict means two guests cannot sit at the same table.
    
    Args:
        filename (str): Path to the conflicts CSV file
        
    Returns:
        dict: Dictionary mapping each guest to a set of guests they conflict with
        
    Notes:
        - Lines starting with '#' are treated as comments and skipped
        - Each line should be: Guest1,Guest2
        - Conflicts are bidirectional (if A conflicts with B, B conflicts with A)
    """
    conflicts = defaultdict(set)
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows and comments
            if not row or row[0].startswith('#'):
                continue
            if len(row) >= 2:
                a, b = row[0].strip(), row[1].strip()
                if a and b:
                    # Add bidirectional conflict
                    conflicts[a].add(b)
                    conflicts[b].add(a)
    return conflicts


def load_groups(filename):
    """
    Load group definitions from a CSV file.
    
    Guests in the same group must all sit at the same table.
    
    Args:
        filename (str): Path to the groups CSV file
        
    Returns:
        tuple: (groups, guest_to_group)
            - groups: dict mapping group names to list of members
            - guest_to_group: dict mapping each guest to their group name
        
    Notes:
        - Lines starting with '#' are treated as comments and skipped
        - Each line should be: GroupName,Member1,Member2,...
        - If a guest appears in multiple groups, a warning is printed
        - If a group name appears multiple times, members are merged
    """
    groups = {}  # group_name -> [list of member names]
    guest_to_group = {}  # guest_name -> group_name
    
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows and comments
            if not row or row[0].startswith('#'):
                continue
            if len(row) >= 2:
                group_name = row[0].strip()
                members = [m.strip() for m in row[1:] if m.strip()]
                
                # Handle duplicate group names by merging members
                if group_name in groups:
                    groups[group_name].extend(members)
                else:
                    groups[group_name] = members
                
                # Track which group each guest belongs to
                for member in members:
                    if member in guest_to_group:
                        # Guest is in multiple groups - warn user
                        print(f"⚠️  WARNING: '{member}' is in multiple groups: "
                              f"'{guest_to_group[member]}' and '{group_name}'")
                    guest_to_group[member] = group_name
    
    return groups, guest_to_group


# =============================================================================
# CORE ALGORITHM FUNCTIONS
# =============================================================================

def can_place(guest, table, table_assignments, conflicts):
    """
    Check if a guest can be placed at a specific table without conflicts.
    
    Args:
        guest (str): The guest to check
        table (int): The table number to check
        table_assignments (dict): Current table assignments {table_num: [guests]}
        conflicts (dict): Conflict mappings from load_conflicts()
        
    Returns:
        bool: True if guest can be placed at the table, False otherwise
    """
    # Check against each guest already seated at this table
    for seated_guest in table_assignments[table]:
        # If there's a conflict between the guest and any seated guest, can't place
        if seated_guest in conflicts.get(guest, set()):
            return False
    return True


def assign_seats(guests, conflicts, groups, guest_to_group, num_tables, seats_per_table):
    """
    Assign guests to tables using a greedy algorithm with constraints.
    
    Algorithm:
    1. Randomly shuffle guests for balanced distribution
    2. For each guest (or their group):
       a. If in a group, get all unassigned group members
       b. Check if group fits at a table (size <= seats_per_table)
       c. Try each table in random order
       d. Check if ALL group members can be placed (no conflicts)
       e. If yes, assign all members to that table
       f. If no table works, mark as unassigned
    
    Args:
        guests (list): List of all guest names
        conflicts (dict): Conflict mappings from load_conflicts()
        groups (dict): Group definitions from load_groups()
        guest_to_group (dict): Guest-to-group mappings from load_groups()
        num_tables (int): Number of tables
        seats_per_table (int): Maximum seats per table
        
    Returns:
        tuple: (table_assignments, unassigned)
            - table_assignments: dict {table_num: [guest_names]}
            - unassigned: list of guests that couldn't be placed
    """
    # Randomize guest order for balanced table distribution
    random.shuffle(guests)
    
    # Initialize data structures
    table_assignments = {i: [] for i in range(num_tables)}
    unassigned = []
    assigned_guests = set()      # Track all assigned guests
    processed_groups = set()     # Track processed groups to avoid duplicates
    
    for guest in guests:
        # Skip if this guest was already assigned as part of a group
        if guest in assigned_guests:
            continue
        
        # ===================================================================
        # DETERMINE WHO TO ASSIGN
        # ===================================================================
        if guest in guest_to_group:
            # This guest is part of a group - assign all unassigned group members
            group_name = guest_to_group[guest]
            
            # Skip if we already processed this entire group
            if group_name in processed_groups:
                continue
            
            group_members = groups[group_name]
            # Only assign members who haven't been assigned yet and are in guest list
            unassigned_members = [
                m for m in group_members 
                if m not in assigned_guests and m in guests
            ]
            
            # Check if group is too large for any table
            if len(unassigned_members) > seats_per_table:
                print(f"⚠️  GROUP TOO LARGE: '{group_name}' has {len(unassigned_members)} "
                      f"members but table only has {seats_per_table} seats")
                unassigned.extend(unassigned_members)
                processed_groups.add(group_name)
                continue
                
        else:
            # Individual guest (not in a group)
            unassigned_members = [guest]
        
        # ===================================================================
        # TRY TO FIND A TABLE FOR THIS GUEST/GROUP
        # ===================================================================
        placed = False
        # Try tables in random order for better distribution
        tables = list(range(num_tables))
        random.shuffle(tables)
        
        for table in tables:
            current_seats = len(table_assignments[table])
            required_seats = len(unassigned_members)
            
            # Check if table has enough capacity
            if current_seats + required_seats > seats_per_table:
                continue
            
            # Check if ALL members can be placed at this table (no conflicts)
            can_place_all = True
            for member in unassigned_members:
                if not can_place(member, table, table_assignments, conflicts):
                    can_place_all = False
                    break
            
            # If all checks pass, assign all members to this table
            if can_place_all:
                for member in unassigned_members:
                    table_assignments[table].append(member)
                    assigned_guests.add(member)
                placed = True
                processed_groups.add(group_name if guest in guest_to_group else None)
                break
        
        # If we couldn't place the guest/group, add to unassigned list
        if not placed:
            for member in unassigned_members:
                if member not in assigned_guests and member not in unassigned:
                    unassigned.append(member)
    
    return table_assignments, unassigned


# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================

def print_seating_chart(table_assignments, num_tables, seats_per_table):
    """
    Print the seating chart in a human-readable format.
    
    Args:
        table_assignments (dict): {table_num: [guest_names]}
        num_tables (int): Total number of tables
        seats_per_table (int): Maximum seats per table
    """
    print("\n" + "=" * 60)
    print("WEDDING SEATING CHART")
    print("=" * 60)
    
    for i in range(num_tables):
        table = table_assignments[i]
        empty_seats = seats_per_table - len(table)
        print(f"\nTable {i+1} ({len(table)}/{seats_per_table} guests, {empty_seats} empty seats):")
        for j, guest in enumerate(table, 1):
            print(f"  Seat {j}: {guest}")
        if empty_seats > 0:
            print(f"  [Seat {len(table)+1}-{seats_per_table}: Empty]")
    
    print("\n" + "=" * 60)


def export_to_csv(table_assignments, num_tables, seats_per_table, filename):
    """
    Export seating chart to a CSV file.
    
    CSV format: Table,Seat,Guest
    - Includes empty seats as "Empty"
    
    Args:
        table_assignments (dict): {table_num: [guest_names]}
        num_tables (int): Total number of tables
        seats_per_table (int): Maximum seats per table
        filename (str): Output CSV file path
    """
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Table', 'Seat', 'Guest'])
        for i in range(num_tables):
            table = table_assignments[i]
            for j, guest in enumerate(table, 1):
                writer.writerow([i+1, j, guest])
            # Add empty seats
            for j in range(len(table)+1, seats_per_table+1):
                writer.writerow([i+1, j, 'Empty'])
    print(f"\n✓ Exported seating chart to {filename}")


def validate_no_conflicts(table_assignments, conflicts):
    """
    Validate that no conflicting guests are seated at the same table.
    
    Args:
        table_assignments (dict): {table_num: [guest_names]}
        conflicts (dict): Conflict mappings from load_conflicts()
        
    Returns:
        list: List of violation strings, empty if no violations
    """
    violations = []
    for table, guests in table_assignments.items():
        # Check all pairs at this table
        for i, g1 in enumerate(guests):
            for g2 in guests[i+1:]:
                # Check if g1 and g2 conflict (handle missing keys safely)
                if g1 in conflicts and g2 in conflicts.get(g1, set()):
                    violations.append(
                        f"Table {table+1}: {g1} and {g2} cannot sit together"
                    )
    return violations


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function - loads data, assigns seats, and outputs results."""
    # Load guest list
    guests = load_guests(GUEST_FILE)
    print(f"Loaded {len(guests)} guests from {GUEST_FILE}")
    
    # Load conflicts
    conflicts = load_conflicts(CONFLICT_FILE)
    conflict_count = sum(len(v) for v in conflicts.values()) // 2
    print(f"Loaded {conflict_count} conflict pairs from {CONFLICT_FILE}")
    
    # Load groups
    groups, guest_to_group = load_groups(GROUP_FILE)
    print(f"Loaded {len(groups)} groups from {GROUP_FILE}")
    for name, members in groups.items():
        print(f"  - {name}: {members}")
    
    # Assign guests to tables
    table_assignments, unassigned = assign_seats(
        guests, conflicts, groups, guest_to_group, NUM_TABLES, SEATS_PER_TABLE
    )
    
    # Print results
    print_seating_chart(table_assignments, NUM_TABLES, SEATS_PER_TABLE)
    
    # Export to CSV
    export_to_csv(table_assignments, NUM_TABLES, SEATS_PER_TABLE, OUTPUT_CSV)
    
    # Validate no conflicts at same table
    violations = validate_no_conflicts(table_assignments, conflicts)
    if violations:
        print("\n⚠️  CONFLICT VIOLATIONS FOUND:")
        for v in violations:
            print(f"  - {v}")
        print("\n  Try running again for a different random arrangement.")
    else:
        print("\n✓ No conflict violations - all guests seated successfully!")
    
    # Report unassigned guests
    if unassigned:
        print(f"\n⚠️  Could not assign: {', '.join(unassigned)}")
        print("  (They conflict with too many people at all tables)")


if __name__ == '__main__':
    main()
