import subprocess
import os
import logging
from pathlib import Path
import json
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class PackageManager:
    def __init__(self):
        self.tex_trees = self.get_tex_trees()
        self.package_cache = {}
        self.missing_packages = set()

    def get_tex_trees(self) -> List[str]:
        """Get all TeX trees from kpsewhich"""
        try:
            result = subprocess.run(['kpsewhich', '--var-value=TEXMF'],
                                    capture_output=True, text=True, check=True)
            trees = []
            for tree in result.stdout.strip().split('!!'):
                tree = tree.strip()
                if tree and os.path.exists(tree):
                    trees.append(tree)
            logger.info(f"Found {len(trees)} TeX trees")
            return trees
        except Exception as e:
            logger.error(f"Error getting TeX trees: {e}")
            return ['/usr/share/texlive/texmf-dist']

    def discover_packages(self) -> Dict[str, str]:
        """Discover all .sty, .cls, .def files in TeX trees"""
        packages = {}
        extensions = ['.sty', '.cls', '.def', '.fd', '.clo']

        for tree in self.tex_trees:
            tex_path = os.path.join(tree, 'tex')
            if os.path.exists(tex_path):
                for root, dirs, files in os.walk(tex_path):
                    for file in files:
                        if any(file.endswith(ext) for ext in extensions):
                            full_path = os.path.join(root, file)
                            packages[file] = full_path

        logger.info(f"Discovered {len(packages)} package files")
        return packages

    def verify_package_findable(self, package_name: str) -> Tuple[bool, str]:
        """Verify if a package can be found by kpsewhich"""
        try:
            result = subprocess.run(['kpsewhich', package_name],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, "Not found by kpsewhich"
        except Exception as e:
            return False, str(e)

    def install_missing_packages(self, package_names: List[str]) -> bool:
        """Attempt to install missing packages via tlmgr"""
        if not package_names:
            return True

        try:
            # Remove extensions for tlmgr
            clean_names = [name.replace('.sty', '').replace('.cls', '')
                           for name in package_names]

            logger.info(f"Attempting to install: {clean_names}")
            result = subprocess.run(['tlmgr', 'install'] + clean_names,
                                    capture_output=True, text=True)

            if result.returncode == 0:
                # Update filename database
                subprocess.run(['mktexlsr'], check=True)
                logger.info(f"Successfully installed packages: {clean_names}")
                return True
            else:
                logger.warning(f"tlmgr install failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error installing packages: {e}")
            return False

    def get_package_info(self) -> Dict:
        """Get comprehensive package information"""
        packages = self.discover_packages()
        findable_count = 0
        missing_packages = []

        # Sample check on common packages
        test_packages = [
            'zref-clever.sty', 'amsmath.sty', 'geometry.sty',
            'babel.sty', 'fontspec.sty', 'xcolor.sty', 'tikz.sty'
        ]

        for package in test_packages:
            found, path = self.verify_package_findable(package)
            if found:
                findable_count += 1
            else:
                missing_packages.append(package)

        return {
            'total_discovered': len(packages),
            'test_packages_found': findable_count,
            'test_packages_total': len(test_packages),
            'missing_test_packages': missing_packages,
            'tex_trees': self.tex_trees
        }

    def ensure_packages_available(self) -> bool:
        """Ensure all common packages are available"""
        info = self.get_package_info()

        if info['missing_test_packages']:
            logger.warning(f"Missing packages: {info['missing_test_packages']}")
            success = self.install_missing_packages(info['missing_test_packages'])
            if success:
                # Re-check after installation
                info = self.get_package_info()
                logger.info(f"After installation - missing: {info['missing_test_packages']}")

        return len(info['missing_test_packages']) == 0