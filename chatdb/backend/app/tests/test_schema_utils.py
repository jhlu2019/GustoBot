"""
Tests for schema_utils.py
"""
import unittest
from unittest.mock import MagicMock, patch
from app.services.schema_utils import (
    is_column_unique_in_table,
    has_composite_primary_key,
    is_junction_table,
    determine_relationship_type
)

class TestSchemaUtils(unittest.TestCase):
    """Test cases for schema_utils.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.inspector = MagicMock()
        self.schema_info = []

    def test_is_column_unique_in_table_primary_key(self):
        """Test is_column_unique_in_table when column is a primary key"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['id']
        }
        self.inspector.get_unique_constraints.return_value = []
        self.inspector.get_indexes.return_value = []

        result = is_column_unique_in_table(self.inspector, 'table', 'id')
        self.assertTrue(result)

    def test_is_column_unique_in_table_unique_constraint(self):
        """Test is_column_unique_in_table when column has a unique constraint"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['other_id']
        }
        self.inspector.get_unique_constraints.return_value = [
            {'column_names': ['email']}
        ]
        self.inspector.get_indexes.return_value = []

        result = is_column_unique_in_table(self.inspector, 'table', 'email')
        self.assertTrue(result)

    def test_is_column_unique_in_table_unique_index(self):
        """Test is_column_unique_in_table when column has a unique index"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['other_id']
        }
        self.inspector.get_unique_constraints.return_value = []
        self.inspector.get_indexes.return_value = [
            {'unique': True, 'column_names': ['username']}
        ]

        result = is_column_unique_in_table(self.inspector, 'table', 'username')
        self.assertTrue(result)

    def test_is_column_unique_in_table_not_unique(self):
        """Test is_column_unique_in_table when column is not unique"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['other_id']
        }
        self.inspector.get_unique_constraints.return_value = []
        self.inspector.get_indexes.return_value = []

        result = is_column_unique_in_table(self.inspector, 'table', 'name')
        self.assertFalse(result)

    def test_has_composite_primary_key_true(self):
        """Test has_composite_primary_key when table has a composite primary key"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['id1', 'id2']
        }

        result = has_composite_primary_key(self.inspector, 'table')
        self.assertTrue(result)

    def test_has_composite_primary_key_false(self):
        """Test has_composite_primary_key when table has a single primary key"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['id']
        }

        result = has_composite_primary_key(self.inspector, 'table')
        self.assertFalse(result)

    def test_is_junction_table_true(self):
        """Test is_junction_table when table is a junction table"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['student_id', 'course_id']
        }
        self.inspector.get_foreign_keys.return_value = [
            {'constrained_columns': ['student_id'], 'referred_table': 'students'},
            {'constrained_columns': ['course_id'], 'referred_table': 'courses'}
        ]
        self.inspector.get_columns.return_value = [
            {'name': 'student_id'},
            {'name': 'course_id'},
            {'name': 'score'}
        ]

        result = is_junction_table(self.inspector, 'scores', self.schema_info)
        self.assertTrue(result)

    def test_is_junction_table_false(self):
        """Test is_junction_table when table is not a junction table"""
        self.inspector.get_pk_constraint.return_value = {
            'constrained_columns': ['id']
        }
        self.inspector.get_foreign_keys.return_value = [
            {'constrained_columns': ['student_id'], 'referred_table': 'students'}
        ]
        self.inspector.get_columns.return_value = [
            {'name': 'id'},
            {'name': 'student_id'},
            {'name': 'name'},
            {'name': 'address'},
            {'name': 'phone'},
            {'name': 'email'}
        ]

        result = is_junction_table(self.inspector, 'table', self.schema_info)
        self.assertFalse(result)

    def test_determine_relationship_type_one_to_one(self):
        """Test determine_relationship_type for one-to-one relationship"""
        # Mock is_junction_table to return False
        with patch('app.services.schema_utils.is_junction_table', return_value=False):
            # Mock is_column_unique_in_table to return True for both columns
            with patch('app.services.schema_utils.is_column_unique_in_table', return_value=True):
                result = determine_relationship_type(
                    self.inspector,
                    'table1',
                    'id',
                    'table2',
                    'table1_id',
                    self.schema_info
                )
                self.assertEqual(result, '1-to-1')

    def test_determine_relationship_type_one_to_many(self):
        """Test determine_relationship_type for one-to-many relationship"""
        # Mock is_junction_table to return False
        with patch('app.services.schema_utils.is_junction_table', return_value=False):
            # Mock is_column_unique_in_table to return True for source and False for target
            def mock_is_unique(inspector, table, column):
                if table == 'table1' and column == 'id':
                    return True
                return False

            with patch('app.services.schema_utils.is_column_unique_in_table', side_effect=mock_is_unique):
                result = determine_relationship_type(
                    self.inspector,
                    'table1',
                    'id',
                    'table2',
                    'table1_id',
                    self.schema_info
                )
                self.assertEqual(result, '1-to-N')

    def test_determine_relationship_type_many_to_one(self):
        """Test determine_relationship_type for many-to-one relationship"""
        # Mock is_junction_table to return False
        with patch('app.services.schema_utils.is_junction_table', return_value=False):
            # Mock is_column_unique_in_table to return False for source and True for target
            def mock_is_unique(inspector, table, column):
                if table == 'table2' and column == 'id':
                    return True
                return False

            with patch('app.services.schema_utils.is_column_unique_in_table', side_effect=mock_is_unique):
                result = determine_relationship_type(
                    self.inspector,
                    'table1',
                    'table2_id',
                    'table2',
                    'id',
                    self.schema_info
                )
                self.assertEqual(result, 'N-to-1')

    def test_determine_relationship_type_many_to_many(self):
        """Test determine_relationship_type for many-to-many relationship"""
        # Mock is_junction_table to return True
        with patch('app.services.schema_utils.is_junction_table', return_value=True):
            result = determine_relationship_type(
                self.inspector,
                'junction_table',
                'table1_id',
                'table1',
                'id',
                self.schema_info
            )
            self.assertEqual(result, 'N-to-M')

if __name__ == '__main__':
    unittest.main()
