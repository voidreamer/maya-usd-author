"""Unit tests for usdUtils module.

Note: These tests require USD (pxr) to be installed. They can be run
in a Maya Python environment or with USD installed separately.
"""

import unittest
from unittest.mock import MagicMock, patch

import sys

# Mock the pxr modules if not available (for CI environments without USD)
if 'pxr' not in sys.modules:
    sys.modules['pxr'] = MagicMock()
    sys.modules['pxr.Usd'] = MagicMock()
    sys.modules['pxr.UsdGeom'] = MagicMock()
    sys.modules['pxr.Sdf'] = MagicMock()

from scripts.maya_usd_editor.usdUtils import (
    PrimPurpose,
    PrimInfo,
    VariantSetInfo,
)


class TestPrimPurpose(unittest.TestCase):
    """Tests for PrimPurpose enum."""

    def test_purpose_values(self):
        """Test that all expected purpose values exist."""
        self.assertEqual(PrimPurpose.DEFAULT.value, "default")
        self.assertEqual(PrimPurpose.RENDER.value, "render")
        self.assertEqual(PrimPurpose.PROXY.value, "proxy")
        self.assertEqual(PrimPurpose.GUIDE.value, "guide")

    def test_purpose_from_value(self):
        """Test creating PrimPurpose from string value."""
        self.assertEqual(PrimPurpose("default"), PrimPurpose.DEFAULT)
        self.assertEqual(PrimPurpose("render"), PrimPurpose.RENDER)


class TestPrimInfo(unittest.TestCase):
    """Tests for PrimInfo dataclass."""

    def test_prim_info_creation(self):
        """Test creating a PrimInfo instance."""
        mock_path = MagicMock()
        info = PrimInfo(
            name="testPrim",
            type_name="Xform",
            kind="component",
            purpose="default",
            path=mock_path
        )

        self.assertEqual(info.name, "testPrim")
        self.assertEqual(info.type_name, "Xform")
        self.assertEqual(info.kind, "component")
        self.assertEqual(info.purpose, "default")
        self.assertEqual(info.path, mock_path)


class TestVariantSetInfo(unittest.TestCase):
    """Tests for VariantSetInfo dataclass."""

    def test_variant_set_info_creation(self):
        """Test creating a VariantSetInfo instance."""
        info = VariantSetInfo(
            name="modelingVariant",
            variants=["low", "mid", "high"],
            current_selection="mid"
        )

        self.assertEqual(info.name, "modelingVariant")
        self.assertEqual(info.variants, ["low", "mid", "high"])
        self.assertEqual(info.current_selection, "mid")


class TestUsdUtilsFunctions(unittest.TestCase):
    """Tests for utility functions with mocked USD objects."""

    def test_get_variant_sets(self):
        """Test get_variant_sets with mocked prim."""
        from scripts.maya_usd_editor.usdUtils import get_variant_sets

        # Create mock prim with variant sets
        mock_vs = MagicMock()
        mock_vs.GetVariantNames.return_value = ["a", "b", "c"]
        mock_vs.GetVariantSelection.return_value = "b"

        mock_variant_sets = MagicMock()
        mock_variant_sets.GetNames.return_value = ["testVariant"]

        mock_prim = MagicMock()
        mock_prim.GetVariantSets.return_value = mock_variant_sets
        mock_prim.GetVariantSet.return_value = mock_vs

        result = get_variant_sets(mock_prim)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "testVariant")
        self.assertEqual(result[0].variants, ["a", "b", "c"])
        self.assertEqual(result[0].current_selection, "b")

    def test_set_variant_selection(self):
        """Test set_variant_selection with mocked prim."""
        from scripts.maya_usd_editor.usdUtils import set_variant_selection

        mock_vs = MagicMock()
        mock_prim = MagicMock()
        mock_prim.GetVariantSet.return_value = mock_vs

        set_variant_selection(mock_prim, "testVariant", "optionA")

        mock_prim.GetVariantSet.assert_called_once_with("testVariant")
        mock_vs.SetVariantSelection.assert_called_once_with("optionA")

    def test_has_payload(self):
        """Test has_payload with mocked prim."""
        from scripts.maya_usd_editor.usdUtils import has_payload

        mock_prim = MagicMock()
        mock_prim.HasPayload.return_value = True

        self.assertTrue(has_payload(mock_prim))
        mock_prim.HasPayload.assert_called_once()

    def test_load_payload(self):
        """Test load_payload with mocked prim."""
        from scripts.maya_usd_editor.usdUtils import load_payload

        mock_prim = MagicMock()
        load_payload(mock_prim)
        mock_prim.Load.assert_called_once()

    def test_unload_payload(self):
        """Test unload_payload with mocked prim."""
        from scripts.maya_usd_editor.usdUtils import unload_payload

        mock_prim = MagicMock()
        unload_payload(mock_prim)
        mock_prim.Unload.assert_called_once()


if __name__ == '__main__':
    unittest.main()
