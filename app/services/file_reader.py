"""
Dosya okuyucu servisi - Strategy Pattern ile farklı dosya formatlarını okur
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd


class FileReaderStrategy(ABC):
    """
    Dosya okuma stratejisi için soyut sınıf.
    Open/Closed Principle: Yeni dosya formatları eklemek için mevcut kodu değiştirmeden
    yeni strategy sınıfları oluşturulabilir.
    """
    
    @abstractmethod
    def can_read(self, file_path: Path) -> bool:
        """Bu strateji verilen dosyayı okuyabilir mi?"""
        pass
    
    @abstractmethod
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Dosyayı okur ve DataFrame olarak döndürür."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Desteklenen dosya uzantıları"""
        pass


class CSVReader(FileReaderStrategy):
    """CSV dosyalarını okur"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.csv', '.tsv', '.txt']
    
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        CSV dosyasını okur.
        Encoding ve delimiter otomatik algılanmaya çalışılır.
        """
        # Delimiter belirleme
        delimiter = kwargs.get('delimiter', None)
        if delimiter is None:
            if file_path.suffix.lower() == '.tsv':
                delimiter = '\t'
            else:
                delimiter = self._detect_delimiter(file_path)
        
        # Encoding belirleme
        encoding = kwargs.get('encoding', None)
        if encoding is None:
            encoding = self._detect_encoding(file_path)
        
        return pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            parse_dates=True
        )
    
    def _detect_delimiter(self, file_path: Path) -> str:
        """Delimiter'ı otomatik algılar"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                
            # Yaygın delimiter'ları kontrol et
            delimiters = [',', ';', '\t', '|']
            counts = {d: first_line.count(d) for d in delimiters}
            
            # En çok kullanılanı seç
            return max(counts, key=counts.get)
        except Exception:
            return ','
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Encoding'i otomatik algılar"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-9', 'cp1254']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'utf-8'


class ExcelReader(FileReaderStrategy):
    """Excel dosyalarını okur (xlsx, xls)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.xlsx', '.xls', '.xlsm', '.xlsb']
    
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Excel dosyasını okur.
        Sheet adı belirtilebilir, varsayılan olarak ilk sheet okunur.
        """
        sheet_name = kwargs.get('sheet_name', 0)
        
        # xls dosyaları için xlrd, xlsx için openpyxl kullan
        if file_path.suffix.lower() == '.xls':
            engine = 'xlrd'
        else:
            engine = 'openpyxl'
        
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine=engine,
            parse_dates=True
        )


class OdsReader(FileReaderStrategy):
    """OpenDocument Spreadsheet dosyalarını okur"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.ods']
    
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        sheet_name = kwargs.get('sheet_name', 0)
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine='odf'
        )


class FileReaderFactory:
    """
    Dosya okuyucu fabrikası.
    Dependency Inversion: Üst seviye modüller somut implementasyonlara değil
    soyutlamalara (FileReaderStrategy) bağlı.
    """
    
    def __init__(self):
        self._strategies: list[FileReaderStrategy] = [
            CSVReader(),
            ExcelReader(),
            OdsReader()
        ]
    
    def register_strategy(self, strategy: FileReaderStrategy) -> None:
        """Yeni bir okuma stratejisi ekler"""
        self._strategies.append(strategy)
    
    def get_reader(self, file_path: Path) -> Optional[FileReaderStrategy]:
        """Dosya için uygun okuyucuyu döndürür"""
        for strategy in self._strategies:
            if strategy.can_read(file_path):
                return strategy
        return None
    
    def read_file(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Dosyayı okur ve DataFrame olarak döndürür"""
        reader = self.get_reader(file_path)
        if reader is None:
            raise ValueError(f"Desteklenmeyen dosya formatı: {file_path.suffix}")
        return reader.read(file_path, **kwargs)
    
    def get_supported_extensions(self) -> list[str]:
        """Tüm desteklenen uzantıları döndürür"""
        extensions = []
        for strategy in self._strategies:
            extensions.extend(strategy.supported_extensions)
        return extensions
    
    def get_file_filter(self) -> str:
        """Dosya seçici için filtre stringi döndürür"""
        all_extensions = self.get_supported_extensions()
        all_pattern = ' '.join(f'*{ext}' for ext in all_extensions)
        
        filters = [f"Tüm Desteklenen Dosyalar ({all_pattern})"]
        
        # Her strateji için ayrı filtre
        filters.append(f"CSV Dosyaları (*.csv *.tsv *.txt)")
        filters.append(f"Excel Dosyaları (*.xlsx *.xls *.xlsm)")
        filters.append(f"Tüm Dosyalar (*)")
        
        return ";;".join(filters)
