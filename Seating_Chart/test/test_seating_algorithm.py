import unittest
import csv
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from seating_algorithm import (
    load_guests, load_conflicts, load_groups,
    can_place, assign_seats, validate_no_conflicts
)


class TestLoadGuests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.guest_file = os.path.join(self.temp_dir, 'guests.csv')
        
    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)
    
    def test_load_guests_basic(self):
        with open(self.guest_file, 'w') as f:
            f.write('Alice\nBob\nCharlie\n')
        guests = load_guests(self.guest_file)
        self.assertEqual(len(guests), 3)
        self.assertIn('Alice', guests)
        self.assertIn('Bob', guests)
        self.assertIn('Charlie', guests)
    
    def test_load_guests_with_blanks(self):
        with open(self.guest_file, 'w') as f:
            f.write('Alice\n\nBob\n\nCharlie\n')
        guests = load_guests(self.guest_file)
        self.assertEqual(len(guests), 3)
        self.assertNotIn('', guests)
    
    def test_load_guests_empty_file(self):
        with open(self.guest_file, 'w') as f:
            f.write('')
        guests = load_guests(self.guest_file)
        self.assertEqual(len(guests), 0)


class TestLoadConflicts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.conflict_file = os.path.join(self.temp_dir, 'conflicts.csv')
        
    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)
    
    def test_load_conflicts_basic(self):
        with open(self.conflict_file, 'w') as f:
            f.write('Alice,Bob\nCharlie,Dave\n')
        conflicts = load_conflicts(self.conflict_file)
        self.assertIn('Bob', conflicts['Alice'])
        self.assertIn('Alice', conflicts['Bob'])
        self.assertIn('Dave', conflicts['Charlie'])
        self.assertEqual(len(conflicts), 4)  # Alice, Bob, Charlie, Dave
    
    def test_load_conflicts_with_comments(self):
        with open(self.conflict_file, 'w') as f:
            f.write('# This is a comment\nAlice,Bob\n# Another comment\n')
        conflicts = load_conflicts(self.conflict_file)
        self.assertEqual(len(conflicts), 2)
        self.assertIn('Bob', conflicts['Alice'])
    
    def test_load_conflicts_empty(self):
        with open(self.conflict_file, 'w') as f:
            f.write('')
        conflicts = load_conflicts(self.conflict_file)
        self.assertEqual(len(conflicts), 0)


class TestLoadGroups(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.group_file = os.path.join(self.temp_dir, 'groups.csv')
        
    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)
    
    def test_load_groups_basic(self):
        with open(self.group_file, 'w') as f:
            f.write('Family,Alice,Bob,Charlie\nFriends,Dave,Eve\n')
        groups, guest_to_group = load_groups(self.group_file)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups['Family']), 3)
        self.assertEqual(guest_to_group['Alice'], 'Family')
        self.assertEqual(guest_to_group['Dave'], 'Friends')
    
    def test_load_groups_with_comments(self):
        with open(self.group_file, 'w') as f:
            f.write('# Comment\nFamily,Alice,Bob\n')
        groups, guest_to_group = load_groups(self.group_file)
        self.assertEqual(len(groups), 1)
    
    def test_load_groups_empty(self):
        with open(self.group_file, 'w') as f:
            f.write('')
        groups, guest_to_group = load_groups(self.group_file)
        self.assertEqual(len(groups), 0)
        self.assertEqual(len(guest_to_group), 0)


class TestCanPlace(unittest.TestCase):
    def test_can_place_no_conflict(self):
        conflicts = {'Alice': set(), 'Bob': set()}
        table_assignments = {0: ['Alice']}
        self.assertTrue(can_place('Bob', 0, table_assignments, conflicts))
    
    def test_can_place_with_conflict(self):
        conflicts = {'Alice': {'Bob'}, 'Bob': {'Alice'}}
        table_assignments = {0: ['Alice']}
        self.assertFalse(can_place('Bob', 0, table_assignments, conflicts))
    
    def test_can_place_empty_table(self):
        conflicts = {}
        table_assignments = {0: []}
        self.assertTrue(can_place('Alice', 0, table_assignments, conflicts))


class TestAssignSeats(unittest.TestCase):
    def test_all_guests_assigned_no_constraints(self):
        guests = ['A', 'B', 'C', 'D', 'E', 'F']
        conflicts = {g: set() for g in guests}
        groups = {}
        guest_to_group = {}
        
        table_assignments, unassigned = assign_seats(
            guests, conflicts, groups, guest_to_group, num_tables=2, seats_per_table=4
        )
        
        all_assigned = []
        for table in table_assignments.values():
            all_assigned.extend(table)
        
        self.assertEqual(len(unassigned), 0)
        self.assertEqual(sorted(all_assigned), sorted(guests))
    
    def test_groups_seated_together(self):
        guests = ['A', 'B', 'C', 'D']
        conflicts = {g: set() for g in guests}
        groups = {'Group1': ['A', 'B']}
        guest_to_group = {'A': 'Group1', 'B': 'Group1'}
        
        table_assignments, unassigned = assign_seats(
            guests, conflicts, groups, guest_to_group, num_tables=2, seats_per_table=4
        )
        
        # Find which table has A, check B is there too
        a_table = None
        b_table = None
        for table, members in table_assignments.items():
            if 'A' in members:
                a_table = table
            if 'B' in members:
                b_table = table
        
        self.assertIsNotNone(a_table)
        self.assertIsNotNone(b_table)
        self.assertEqual(a_table, b_table, "Group members A and B should be at same table")
    
    def test_conflicts_respected(self):
        guests = ['A', 'B', 'C', 'D']
        conflicts = {'A': {'B'}, 'B': {'A'}, 'C': set(), 'D': set()}
        groups = {}
        guest_to_group = {}
        
        table_assignments, unassigned = assign_seats(
            guests, conflicts, groups, guest_to_group, num_tables=2, seats_per_table=4
        )
        
        # Check A and B are not at the same table
        a_table = None
        b_table = None
        for table, members in table_assignments.items():
            if 'A' in members:
                a_table = table
            if 'B' in members:
                b_table = table
        
        self.assertIsNotNone(a_table)
        self.assertIsNotNone(b_table)
        self.assertNotEqual(a_table, b_table, "A and B have a conflict and should not be at same table")
    
    def test_group_too_large(self):
        guests = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        conflicts = {g: set() for g in guests}
        groups = {'BigGroup': guests}
        guest_to_group = {g: 'BigGroup' for g in guests}
        
        table_assignments, unassigned = assign_seats(
            guests, conflicts, groups, guest_to_group, num_tables=2, seats_per_table=4
        )
        
        # All should be unassigned since group is too large
        self.assertEqual(len(unassigned), 9)
    
    def test_empty_input(self):
        table_assignments, unassigned = assign_seats(
            [], {}, {}, {}, num_tables=1, seats_per_table=8
        )
        self.assertEqual(len(table_assignments), 1)
        self.assertEqual(len(table_assignments[0]), 0)
        self.assertEqual(len(unassigned), 0)


class TestValidateNoConflicts(unittest.TestCase):
    def test_no_violations(self):
        table_assignments = {0: ['A', 'B'], 1: ['C', 'D']}
        conflicts = {'A': set(), 'B': set(), 'C': set(), 'D': set()}
        violations = validate_no_conflicts(table_assignments, conflicts)
        self.assertEqual(len(violations), 0)
    
    def test_with_violations(self):
        table_assignments = {0: ['A', 'B'], 1: ['C', 'D']}
        conflicts = {'A': {'B'}, 'B': {'A'}, 'C': set(), 'D': set()}
        violations = validate_no_conflicts(table_assignments, conflicts)
        self.assertEqual(len(violations), 1)
        self.assertIn('Table 1', violations[0])
        self.assertIn('A and B', violations[0])


if __name__ == '__main__':
    unittest.main()
