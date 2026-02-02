"""
Dosya okuma/yazma servisi - Strategy Pattern ile farklı dosya formatlarını yönetir
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd


class FileIOStrategy(ABC):
    """
    Dosya okuma/yazma stratejisi için soyut sınıf.
    Tüm handler'lar bu sınıftan türer.
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Desteklenen dosya uzantıları (hem okuma hem yazma)"""
        pass
    
    @property
    @abstractmethod
    def filter_name(self) -> str:
        """Dosya seçici için filtre adı (örn: 'CSV Dosyaları')"""
        pass
    
    @property
    def readable_extensions(self) -> list[str]:
        """Okunabilir uzantılar, varsayılan olarak supported_extensions"""
        return self.supported_extensions
    
    @property
    def writable_extensions(self) -> list[str]:
        """Yazılabilir uzantılar, varsayılan olarak supported_extensions"""
        return self.supported_extensions
    
    def can_read(self, file_path: Path) -> bool:
        """Bu strateji verilen dosyayı okuyabilir mi?"""
        return file_path.suffix.lower() in self.readable_extensions
    
    def can_write(self, file_path: Path) -> bool:
        """Bu strateji verilen dosyaya yazabilir mi?"""
        return file_path.suffix.lower() in self.writable_extensions
    
    @abstractmethod
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Dosyayı okur ve DataFrame olarak döndürür."""
        pass
    
    @abstractmethod
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """DataFrame'i dosyaya yazar. Başarılı ise True döner."""
        pass


class CSVHandler(FileIOStrategy):
    """CSV dosyalarını okur ve yazar"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.csv', '.tsv', '.txt']
    
    @property
    def filter_name(self) -> str:
        return "CSV Dosyaları"
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        CSV dosyasını okur.
        Encoding ve delimiter otomatik algılanmaya çalışılır.
        """
        delimiter = kwargs.get('delimiter', None)
        if delimiter is None:
            if file_path.suffix.lower() == '.tsv':
                delimiter = '\t'
            else:
                delimiter = self._detect_delimiter(file_path)
        
        encoding = kwargs.get('encoding', None)
        if encoding is None:
            encoding = self._detect_encoding(file_path)
        
        return pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            parse_dates=True
        )
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        CSV dosyasına yazar.
        Excel uyumluluğu için utf-8-sig encoding kullanır.
        TSV için tab delimiter kullanır.
        """
        try:
            delimiter = kwargs.get('delimiter', None)
            if delimiter is None:
                if file_path.suffix.lower() == '.tsv':
                    delimiter = '\t'
                else:
                    delimiter = ','
            
            df.to_csv(file_path, index=False, encoding='utf-8-sig', sep=delimiter)
            return True
        except Exception as e:
            print(f"CSV yazma hatası: {e}")
            raise e
    
    def _detect_delimiter(self, file_path: Path) -> str:
        """Delimiter'ı otomatik algılar"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                
            delimiters = [',', ';', '\t', '|']
            counts = {d: first_line.count(d) for d in delimiters}
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


class ExcelHandler(FileIOStrategy):
    """Excel dosyalarını okur ve yazar (xlsx, xls, xlsm, xlsb)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.xlsx', '.xls', '.xlsm', '.xlsb']
    
    @property
    def filter_name(self) -> str:
        return "Excel Dosyaları"
    
    @property
    def writable_extensions(self) -> list[str]:
        """Sadece xlsx yazılabilir"""
        return ['.xlsx']
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Excel dosyasını okur.
        Sheet adı belirtilebilir, varsayılan olarak ilk sheet okunur.
        """
        sheet_name = kwargs.get('sheet_name', 0)
        
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


class ODSHandler(FileIOStrategy):
    """OpenDocument Spreadsheet dosyalarını okur ve yazar (LibreOffice/OpenOffice)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.ods']
    
    @property
    def filter_name(self) -> str:
        return "OpenDocument Dosyaları"
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        ODS dosyasını okur.
        odfpy motorunu kullanır.
        """
        sheet_name = kwargs.get('sheet_name', 0)
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine='odf',
            parse_dates=True
        )
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        ODS dosyasına yazar.
        odfpy motorunu kullanır.
        Tarih sütunları için uygun format uygulanır.
        """
        try:
            # DataFrame'in bir kopyasını oluştur
            df_copy = df.copy()
            
            # Tarih sütunlarını string formatına çevir (ODS uyumluluğu için)
            date_columns = df_copy.select_dtypes(include=['datetime64[ns]', 'datetime64']).columns
            for col in date_columns:
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
            
            df_copy.to_excel(file_path, index=False, engine='odf')
            return True
        except Exception as e:
            print(f"ODS yazma hatası: {e}")
            raise e


class JSONHandler(FileIOStrategy):
    """JSON dosyalarını okur ve yazar"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.json']
    
    @property
    def filter_name(self) -> str:
        return "JSON Dosyaları"
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        JSON dosyasını okur.
        orient parametresi ile farklı JSON yapıları desteklenir.
        """
        orient = kwargs.get('orient', None)
        encoding = kwargs.get('encoding', 'utf-8')
        
        # orient belirtilmemişse otomatik algıla
        if orient is None:
            orient = self._detect_orient(file_path, encoding)
        
        return pd.read_json(
            file_path,
            orient=orient,
            encoding=encoding,
            convert_dates=True
        )
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        JSON dosyasına yazar.
        Varsayılan olarak 'records' formatında yazar (dizi içinde objeler).
        """
        try:
            orient = kwargs.get('orient', 'records')
            indent = kwargs.get('indent', 2)
            force_ascii = kwargs.get('force_ascii', False)
            
            df.to_json(
                file_path,
                orient=orient,
                indent=indent,
                force_ascii=force_ascii,
                date_format='iso'
            )
            return True
        except Exception as e:
            print(f"JSON yazma hatası: {e}")
            raise e
    
    def _detect_orient(self, file_path: Path, encoding: str) -> str:
        """JSON yapısını otomatik algılar"""
        import json
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    return 'records'
                return 'values'
            elif isinstance(data, dict):
                first_value = next(iter(data.values()), None)
                if isinstance(first_value, dict):
                    return 'index'
                elif isinstance(first_value, list):
                    return 'columns'
                return 'split'
        except Exception:
            pass
        return 'records'


class PickleHandler(FileIOStrategy):
    """Python Pickle dosyalarını okur ve yazar (hızlı serileştirme)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.pkl', '.pickle']
    
    @property
    def filter_name(self) -> str:
        return "Pickle Dosyaları"
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Pickle dosyasını okur.
        Compression otomatik algılanır.
        """
        compression = kwargs.get('compression', 'infer')
        return pd.read_pickle(file_path, compression=compression)
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        Pickle dosyasına yazar.
        Opsiyonel olarak sıkıştırma destekler.
        """
        try:
            compression = kwargs.get('compression', 'infer')
            protocol = kwargs.get('protocol', 4)
            df.to_pickle(file_path, compression=compression, protocol=protocol)
            return True
        except Exception as e:
            print(f"Pickle yazma hatası: {e}")
            raise e


class ParquetHandler(FileIOStrategy):
    """Apache Parquet dosyalarını okur ve yazar (büyük veri için optimize)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.parquet', '.pq']
    
    @property
    def filter_name(self) -> str:
        return "Parquet Dosyaları"
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Parquet dosyasını okur.
        pyarrow veya fastparquet motorunu kullanır.
        """
        engine = kwargs.get('engine', 'auto')
        columns = kwargs.get('columns', None)
        
        return pd.read_parquet(
            file_path,
            engine=engine,
            columns=columns
        )
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        Parquet dosyasına yazar.
        Sıkıştırma varsayılan olarak snappy kullanır.
        Sütun isimleri otomatik olarak string'e dönüştürülür.
        """
        try:
            engine = kwargs.get('engine', 'auto')
            compression = kwargs.get('compression', 'snappy')
            # Parquet karışık tip sütun isimlerini desteklemez, string'e çevir
            df_copy = df.copy()
            df_copy.columns = df_copy.columns.astype(str)
            df_copy.to_parquet(
                file_path,
                engine=engine,
                compression=compression,
                index=False
            )
            return True
        except Exception as e:
            print(f"Parquet yazma hatası: {e}")
            raise e


class FeatherHandler(FileIOStrategy):
    """Apache Arrow Feather dosyalarını okur ve yazar (hızlı I/O)"""
    
    @property
    def supported_extensions(self) -> list[str]:
        return ['.feather', '.ftr']
    
    @property
    def filter_name(self) -> str:
        return "Feather Dosyaları"
    
    def read(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Feather dosyasını okur.
        Çok hızlı okuma performansı sağlar.
        """
        columns = kwargs.get('columns', None)
        return pd.read_feather(file_path, columns=columns)
    
    def write(self, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """
        Feather dosyasına yazar.
        Çok hızlı yazma performansı sağlar.
        Sütun isimleri otomatik olarak string'e dönüştürülür.
        """
        try:
            compression = kwargs.get('compression', 'zstd')
            # Feather karışık tip sütun isimlerini desteklemez, string'e çevir
            df_copy = df.copy()
            df_copy.columns = df_copy.columns.astype(str)
            df_copy.to_feather(file_path, compression=compression)
            return True
        except Exception as e:
            print(f"Feather yazma hatası: {e}")
            raise e


class FileIORegistry:
    """
    Merkezi dosya I/O kayıt sistemi.
    Hem okuma hem yazma işlemlerini yönetir.
    """
    
    _handlers: list[FileIOStrategy] = []
    
    @classmethod
    def register(cls, handler: FileIOStrategy) -> None:
        """Yeni bir handler kaydeder"""
        cls._handlers.append(handler)
    
    @classmethod
    def get_handlers(cls) -> list[FileIOStrategy]:
        """Kayıtlı tüm handler'ları döndürür"""
        return cls._handlers.copy()
    
    # ============ Reader İşlemleri ============
    
    @classmethod
    def get_reader(cls, file_path: Path) -> Optional[FileIOStrategy]:
        """Dosya için uygun okuyucuyu döndürür"""
        for handler in cls._handlers:
            if handler.can_read(file_path):
                return handler
        return None
    
    @classmethod
    def read_file(cls, file_path: Path, **kwargs) -> pd.DataFrame:
        """Dosyayı okur ve DataFrame olarak döndürür"""
        reader = cls.get_reader(file_path)
        if reader is None:
            raise ValueError(f"Desteklenmeyen dosya formatı: {file_path.suffix}")
        return reader.read(file_path, **kwargs)
    
    @classmethod
    def get_readable_extensions(cls) -> list[str]:
        """Tüm okunabilir uzantıları döndürür"""
        extensions = []
        for handler in cls._handlers:
            extensions.extend(handler.readable_extensions)
        return extensions
    
    @classmethod
    def get_file_filter(cls) -> str:
        """Dosya seçici için filtre stringi döndürür (handler'lardan dinamik)"""
        all_extensions = cls.get_readable_extensions()
        all_pattern = ' '.join(f'*{ext}' for ext in all_extensions)
        
        filters = [f"Tüm Desteklenen Dosyalar ({all_pattern})"]
        
        # Her handler için dinamik filtre oluştur
        for handler in cls._handlers:
            exts = handler.readable_extensions
            pattern = ' '.join(f'*{ext}' for ext in exts)
            filters.append(f"{handler.filter_name} ({pattern})")
        
        filters.append("Tüm Dosyalar (*)")
        
        return ";;".join(filters)
    
    # ============ Writer İşlemleri ============
    
    @classmethod
    def get_writer(cls, file_path: Path) -> Optional[FileIOStrategy]:
        """Dosya için uygun yazıcıyı döndürür"""
        for handler in cls._handlers:
            if handler.can_write(file_path):
                return handler
        return None
    
    @classmethod
    def write_file(cls, df: pd.DataFrame, file_path: Path, **kwargs) -> bool:
        """DataFrame'i dosyaya yazar"""
        writer = cls.get_writer(file_path)
        if writer is None:
            raise ValueError(f"Desteklenmeyen dosya formatı: {file_path.suffix}")
        return writer.write(df, file_path, **kwargs)
    
    @classmethod
    def get_writable_extensions(cls) -> list[str]:
        """Tüm yazılabilir uzantıları döndürür"""
        extensions = []
        for handler in cls._handlers:
            extensions.extend(handler.writable_extensions)
        return extensions
    
    @classmethod
    def _build_descriptor(cls, handler: FileIOStrategy) -> Optional[dict]:
        """Tek bir handler için descriptor oluşturur"""
        exts = [e.lower() for e in handler.writable_extensions]
        if not exts:
            return None
        
        patterns = ';'.join(f'*{e}' for e in exts)
        
        return {
            'name': f"{', '.join(exts)}",
            'filter': f"{handler.__class__.__name__} ({patterns})",
            'default': exts[0],
            'extensions': exts,
        }
    
    @classmethod
    def get_format_descriptors(cls) -> list[dict]:
        """Tüm handler'lar için UI descriptor listesi döndürür"""
        descriptors = []
        for handler in cls._handlers:
            desc = cls._build_descriptor(handler)
            if desc:
                descriptors.append(desc)
        return descriptors
    
    @classmethod
    def get_descriptor_by_extension(cls, extension: str) -> Optional[dict]:
        """Verilen uzantı için uygun descriptor'ı döndürür"""
        ext = extension.lower().lstrip('.')
        
        for handler in cls._handlers:
            handler_exts = [e.lower().lstrip('.') for e in handler.writable_extensions]
            if ext in handler_exts:
                return cls._build_descriptor(handler)
        
        return None
    
    @classmethod
    def is_extension_supported(cls, extension: str) -> bool:
        """Verilen uzantının yazılabilir olup olmadığını kontrol eder"""
        return cls.get_descriptor_by_extension(extension) is not None


# ============ Handler Registrations (Open/Closed Principle) ============
FileIORegistry.register(CSVHandler())
FileIORegistry.register(ExcelHandler())
FileIORegistry.register(ODSHandler())
FileIORegistry.register(JSONHandler())
FileIORegistry.register(PickleHandler())
FileIORegistry.register(ParquetHandler())
FileIORegistry.register(FeatherHandler())
