import csv
import random
from collections import defaultdict

# Configuration
NUM_TABLES = 9
SEATS_PER_TABLE = 8
GUEST_FILE = 'data/Guest List for Final - Sheet1.csv'
CONFLICT_FILE = 'data/conflicts.csv'
GROUP_FILE = 'data/groups.csv'


def load_guests(filename):
    """Load guest list from CSV."""
    guests = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                guests.append(row[0].strip())
    return guests


def load_conflicts(filename):
    """Load conflict pairs from CSV."""
    conflicts = defaultdict(set)
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            if len(row) >= 2:
                a, b = row[0].strip(), row[1].strip()
                if a and b:
                    conflicts[a].add(b)
                    conflicts[b].add(a)
    return conflicts


def load_groups(filename):
    """Load groups that must sit together from CSV."""
    groups = defaultdict(list)  # group_name -> [members]
    guest_to_group = {}  # guest -> group_name
    
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            if len(row) >= 2:
                group_name = row[0].strip()
                members = [m.strip() for m in row[1:] if m.strip()]
                groups[group_name] = members
                for member in members:
                    guest_to_group[member] = group_name
    
    return groups, guest_to_group


def get_group_size(guest, guest_to_group):
    """Get the size of the group this guest belongs to."""
    if guest not in guest_to_group:
        return 1
    group_name = guest_to_group[guest]
    return len(guest_to_group[guest]) if guest in guest_to_group else 1


def can_place(guest, table, table_assignments, conflicts):
    """Check if guest can be placed at this table without conflicts."""
    for seated_guest in table_assignments[table]:
        if seated_guest in conflicts[guest]:
            return False
    return True


def assign_seats(guests, conflicts, groups, guest_to_group, num_tables, seats_per_table):
    """
    Assign guests to tables using a greedy algorithm with conflict and group checking.
    Groups are assigned together - all members must fit at the same table.
    Shuffles guests randomly for better distribution.
    """
    random.shuffle(guests)
    
    table_assignments = {i: [] for i in range(num_tables)}
    unassigned = []
    assigned_groups = set()
    
    for guest in guests:
        # Skip if already assigned as part of a group
        if guest in assigned_groups:
            continue
        
        # Determine if this is a group assignment
        if guest in guest_to_group:
            group_name = guest_to_group[guest]
            group_members = groups[group_name]
            # Only process if not already assigned
            unassigned_members = [m for m in group_members if m not in assigned_groups]
            if not unassigned_members:
                continue
        else:
            unassigned_members = [guest]
        
        placed = False
        # Try each table in random order
        tables = list(range(num_tables))
        random.shuffle(tables)
        
        for table in tables:
            current_seats = len(table_assignments[table])
            required_seats = len(unassigned_members)
            
            if current_seats + required_seats > seats_per_table:
                continue
            
            # Check if all members can be placed at this table
            can_place_all = True
            for member in unassigned_members:
                if not can_place(member, table, table_assignments, conflicts):
                    can_place_all = False
                    break
            
            if can_place_all:
                for member in unassigned_members:
                    table_assignments[table].append(member)
                    assigned_groups.add(member)
                placed = True
                break
        
        if not placed:
            unassigned.extend(unassigned_members)
    
    return table_assignments, unassigned


def print_seating_chart(table_assignments, num_tables, seats_per_table):
    """Print the seating chart in a readable format."""
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


def validate_no_conflicts(table_assignments, conflicts):
    """Validate that no conflicts are seated together."""
    violations = []
    for table, guests in table_assignments.items():
        for i, g1 in enumerate(guests):
            for g2 in guests[i+1:]:
                if g2 in conflicts[g1]:
                    violations.append(f"Table {table+1}: {g1} and {g2} cannot sit together")
    return violations


def main():
    guests = load_guests(GUEST_FILE)
    print(f"Loaded {len(guests)} guests from {GUEST_FILE}")
    
    conflicts = load_conflicts(CONFLICT_FILE)
    print(f"Loaded {sum(len(v) for v in conflicts.values()) // 2} conflict pairs from {CONFLICT_FILE}")
    
    groups, guest_to_group = load_groups(GROUP_FILE)
    print(f"Loaded {len(groups)} groups from {GROUP_FILE}")
    for name, members in groups.items():
        print(f"  - {name}: {members}")
    
    table_assignments, unassigned = assign_seats(
        guests, conflicts, groups, guest_to_group, NUM_TABLES, SEATS_PER_TABLE
    )
    
    # Print results
    print_seating_chart(table_assignments, NUM_TABLES, SEATS_PER_TABLE)
    
    # Validate
    violations = validate_no_conflicts(table_assignments, conflicts)
    if violations:
        print("\n⚠️  CONFLICT VIOLATIONS FOUND:")
        for v in violations:
            print(f"  - {v}")
        print("\n  Try running again for a different random arrangement.")
    else:
        print("\n✓ No conflict violations - all guests seated successfully!")
    
    if unassigned:
        print(f"\n⚠️  Could not assign: {', '.join(unassigned)}")
        print("  (They conflict with too many people at all tables)")


if __name__ == '__main__':
    main()
