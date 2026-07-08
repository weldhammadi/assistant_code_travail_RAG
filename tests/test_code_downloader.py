import pytest
from pathlib import Path
from unittest.mock import patch
from data_prep.code_downloader import CodeTravailDownloader

class TestCodeTravailDownloader:
    
    def test_source_url_formatting(self, tmp_path):
        """Vérifie que l'URL Légifrance est correctement formatée avec l'ID du texte."""
        downloader = CodeTravailDownloader(
            source_url_template="https://example.com/{legi_id}.json",
            legi_id="LEGITEXT000006072050",
            cache_dir=tmp_path
        )
        assert downloader.source_url == "https://example.com/LEGITEXT000006072050.json"

    @patch("urllib.request.urlretrieve")
    def test_download_forces_network_call_when_cache_missing(self, mock_urlretrieve, tmp_path):
        """Vérifie qu'un appel réseau est fait si le fichier n'est pas en cache."""
        downloader = CodeTravailDownloader("http://test.com/{legi_id}", "KALITEXT123", tmp_path)
        
        path = downloader.download(force=False)
        
        mock_urlretrieve.assert_called_once_with("http://test.com/KALITEXT123", tmp_path / "KALITEXT123.json")
        assert path == tmp_path / "KALITEXT123.json"

    @patch("urllib.request.urlretrieve")
    def test_download_uses_cache_if_exists(self, mock_urlretrieve, tmp_path):
        """Vérifie que le cache local est utilisé s'il existe (pas d'appel réseau)."""
        cache_file = tmp_path / "KALITEXT123.json"
        cache_file.write_text("{}", encoding="utf-8")
        
        downloader = CodeTravailDownloader("http://test.com/{legi_id}", "KALITEXT123", tmp_path)
        path = downloader.download(force=False)
        
        mock_urlretrieve.assert_not_called()
        assert path == cache_file