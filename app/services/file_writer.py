"""
Dosya yazma servisi - Strategy Pattern ile farklı dosya formatlarına yazar
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd


class FileWriterStrategy(ABC):
    """
    Dosya yazma stratejisi için soyut sınıf.
    Open/Closed Principle: Yeni dosya formatları eklemek için mevcut kodu değiştirmeden
    yeni strategy sınıfları oluşturulabilir.
    """
    
    @abstractmethod
    def can_write(self, file_path: Path) -> bool:
        """Bu strateji verilen dosyaya yazabilir mi?"""
        pass
    
    @abstractmethod
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """DataFrame'i dosyaya yazar. Başarılı ise True döner."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Desteklenen dosya uzantıları"""
        pass


class CSVWriter(FileWriterStrategy):
    """CSV dosyalarına yazar"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.csv']
    
    def can_write(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        CSV dosyasına yazar.
        Excel uyumluluğu için utf-8-sig encoding kullanır.
        """
        try:
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"CSV yazma hatası: {e}")
            raise e


class ExcelWriter(FileWriterStrategy):
    """Excel dosyalarına yazar (xlsx)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.xlsx']
    
    def can_write(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        Excel dosyasına yazar.
        openpyxl motorunu kullanır.
        """
        try:
            df.to_excel(file_path, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Excel yazma hatası: {e}")
            raise e


class FileWriterFactory:
    """
    Dosya yazıcı fabrikası.
    """
    
    def __init__(self):
        self._strategies: list[FileWriterStrategy] = [
            ExcelWriter(),
            CSVWriter()
        ]
    
    def register_strategy(self, strategy: FileWriterStrategy) -> None:
        """Yeni bir yazma stratejisi ekler"""
        self._strategies.append(strategy)
    
    def get_writer(self, file_path: Path) -> Optional[FileWriterStrategy]:
        """Dosya için uygun yazıcıyı döndürür"""
        for strategy in self._strategies:
            if strategy.can_write(file_path):
                return strategy
        return None
    
    def write_file(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """DataFrame'i dosyaya yazar"""
        writer = self.get_writer(file_path)
        if writer is None:
            raise ValueError(f"Desteklenmeyen dosya formatı: {file_path.suffix}")
        return writer.write(df, file_path, **kwargs)
    
    def get_supported_extensions(self) -> list[str]:
        """Tüm desteklenen uzantıları döndürür"""
        extensions = []
        for strategy in self._strategies:
            extensions.extend(strategy.supported_extensions)
        return extensions

    def _build_descriptor(self, strategy: FileWriterStrategy) -> Optional[dict]:
        """Tek bir strateji için descriptor oluşturur (SRP).
        
        Returns:
            Descriptor dict veya None (uzantı yoksa)
        """
        exts = [e.lower() for e in strategy.supported_extensions]
        if not exts:
            return None
        
        patterns = ';'.join(f'*{e}' for e in exts)
        
        return {
            'name': f"{', '.join(exts)}",
            'filter': f"{strategy.__class__.__name__} ({patterns})",
            'default': exts[0],
            'extensions': exts,
        }
    
    def get_format_descriptors(self) -> list[dict]:
        """Tüm stratejiler için UI descriptor listesi döndürür.
        
        Returns:
            Her biri name, filter, default, extensions içeren dict listesi
        """
        descriptors = []
        for strategy in self._strategies:
            desc = self._build_descriptor(strategy)
            if desc:
                descriptors.append(desc)
        return descriptors
    
    def get_descriptor_by_extension(self, extension: str) -> Optional[dict]:
        """Verilen uzantı için uygun descriptor'ı döndürür.
        
        Args:
            extension: Dosya uzantısı (örn. 'csv', '.csv', 'xlsx')
            
        Returns:
            Descriptor dict veya None (desteklenmiyorsa)
        """
        # Uzantıyı normalize et (.csv -> csv)
        ext = extension.lower().lstrip('.')
        
        for strategy in self._strategies:
            strategy_exts = [e.lower().lstrip('.') for e in strategy.supported_extensions]
            if ext in strategy_exts:
                return self._build_descriptor(strategy)
        
        return None
    
    def is_extension_supported(self, extension: str) -> bool:
        """Verilen uzantının desteklenip desteklenmediğini kontrol eder.
        
        Args:
            extension: Dosya uzantısı (örn. 'csv', '.csv')
            
        Returns:
            True eğer destekleniyorsa
        """
        return self.get_descriptor_by_extension(extension) is not None
