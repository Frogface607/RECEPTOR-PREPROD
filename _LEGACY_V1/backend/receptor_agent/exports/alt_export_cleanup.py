"""
ALT Export Cleanup Module
Unified validation and cleanup system for all export pipelines

Обеспечивает:
- Анализ архивов на предмет дублей и невалидных TTK
- Автоматическая очистка перед экспортом
- Валидация обязательного состава (Dish-Skeletons, Product-Skeletons, reference TTK)
- Удаление superfluous files из архивов
"""

import io
import json
import hashlib
import logging
import zipfile
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class TTKValidationError(Exception):
    """Ошибка валидации TTK"""
    pass


class ArchiveAnalysisResult:
    """Результат анализа архива"""
    
    def __init__(self):
        self.duplicate_ttks: List[Dict[str, Any]] = []
        self.invalid_ttks: List[Dict[str, Any]] = []
        self.superfluous_files: List[str] = []
        self.missing_components: List[str] = []
        self.valid_components: List[str] = []
        self.content_hashes: Dict[str, str] = {}
        self.cleanup_actions: List[str] = []
        
    def has_issues(self) -> bool:
        """Проверка наличия проблем в архиве"""
        return (len(self.duplicate_ttks) > 0 or 
                len(self.invalid_ttks) > 0 or 
                len(self.superfluous_files) > 0 or
                len(self.missing_components) > 0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить краткую сводку анализа"""
        return {
            "has_issues": self.has_issues(),
            "duplicates_count": len(self.duplicate_ttks),
            "invalid_count": len(self.invalid_ttks),
            "superfluous_count": len(self.superfluous_files),
            "missing_components": self.missing_components,
            "valid_components": self.valid_components,
            "cleanup_actions_count": len(self.cleanup_actions)
        }


class ALTExportValidator:
    """
    Главный валидатор ALT Export Pipeline
    
    Функции:
    1. Анализ архивов на дубли и ошибки
    2. Автоматическая очистка перед экспортом  
    3. Валидация обязательного состава
    4. Logging всех операций очистки
    """
    
    # Обязательные компоненты для полного iiko экспорта
    REQUIRED_COMPONENTS = {
        "iiko_TTK.xlsx",           # Reference TTK - всегда обязателен
        "Dish-Skeletons.xlsx",     # Dish skeletons - если есть missing dishes
        "Product-Skeletons.xlsx"   # Product skeletons - если есть missing products
    }
    
    # Допустимые файлы в архиве
    ALLOWED_FILE_PATTERNS = [
        r"^iiko_TTK\.xlsx$",
        r"^Dish-Skeletons\.xlsx$", 
        r"^Product-Skeletons\.xlsx$",
        r"^.*\.xlsx$"  # Другие XLSX файлы (для расширяемости)
    ]
    
    # Запрещенные файлы (superfluous)
    SUPERFLUOUS_PATTERNS = [
        r"^\.DS_Store$",           # macOS system files
        r"^Thumbs\.db$",           # Windows system files
        r"^.*\.tmp$",              # Temporary files
        r"^.*\.log$",              # Log files
        r"^.*\.bak$",              # Backup files
        r"^__MACOSX/",             # macOS resource forks
        r"^\..*",                  # Hidden files
    ]
    
    def __init__(self):
        self.cleanup_stats = {
            "total_processed": 0,
            "duplicates_removed": 0,
            "invalid_removed": 0,
            "superfluous_removed": 0,
            "archives_cleaned": 0
        }
    
    def analyze_archive(self, zip_buffer: io.BytesIO, 
                       context: str = "unknown") -> ArchiveAnalysisResult:
        """
        Полный анализ ZIP архива
        
        Args:
            zip_buffer: ZIP файл для анализа
            context: Контекст операции (для логирования)
            
        Returns:
            ArchiveAnalysisResult с найденными проблемами
        """
        result = ArchiveAnalysisResult()
        
        try:
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                file_list = zf.namelist()
                
                logger.info(f"ALT Export Cleanup: Analyzing archive ({context}) with {len(file_list)} files")
                
                # 1. Проверка на superfluous files
                result.superfluous_files = self._find_superfluous_files(file_list)
                
                # 2. Анализ TTK файлов на дубли и валидность
                ttk_files = [f for f in file_list if f.endswith('.xlsx')]
                ttk_analysis = self._analyze_ttk_files(zf, ttk_files)
                result.duplicate_ttks = ttk_analysis['duplicates']
                result.invalid_ttks = ttk_analysis['invalid']
                result.content_hashes = ttk_analysis['hashes']
                
                # 3. Проверка обязательных компонентов
                result.missing_components = self._check_required_components(file_list)
                result.valid_components = [f for f in file_list 
                                         if f in self.REQUIRED_COMPONENTS and f not in result.missing_components]
                
                # 4. Генерация списка cleanup actions
                result.cleanup_actions = self._generate_cleanup_actions(result)
                
                logger.info(f"Analysis complete: {result.get_summary()}")
                
        except Exception as e:
            logger.error(f"Archive analysis failed ({context}): {e}")
            raise TTKValidationError(f"Archive analysis failed: {str(e)}")
            
        return result
    
    def _find_superfluous_files(self, file_list: List[str]) -> List[str]:
        """Поиск superfluous files"""
        superfluous = []
        
        for file_path in file_list:
            # Проверяем по запрещенным паттернам
            for pattern in self.SUPERFLUOUS_PATTERNS:
                if re.match(pattern, file_path, re.IGNORECASE):
                    superfluous.append(file_path)
                    break
            else:
                # Проверяем что файл соответствует разрешенным паттернам
                is_allowed = False
                for pattern in self.ALLOWED_FILE_PATTERNS:
                    if re.match(pattern, file_path, re.IGNORECASE):
                        is_allowed = True
                        break
                
                if not is_allowed:
                    superfluous.append(file_path)
                    
        return superfluous
    
    def _analyze_ttk_files(self, zf: zipfile.ZipFile, 
                          ttk_files: List[str]) -> Dict[str, Any]:
        """Анализ TTK файлов на дубли и валидность"""
        
        duplicates = []
        invalid = []
        hashes = {}
        seen_ids = set()
        seen_names = set()
        
        for file_path in ttk_files:
            try:
                # Получаем content hash для дедупликации
                file_content = zf.read(file_path)
                content_hash = hashlib.md5(file_content).hexdigest()
                hashes[file_path] = content_hash
                
                # Парсим метаданные из файла (если возможно)
                metadata = self._extract_ttk_metadata(file_content, file_path)
                
                # Проверка на дубли по ID
                if metadata.get('dish_id') and metadata['dish_id'] in seen_ids:
                    duplicates.append({
                        "file": file_path,
                        "type": "duplicate_id",
                        "dish_id": metadata['dish_id'],
                        "dish_name": metadata.get('dish_name', 'Unknown'),
                        "content_hash": content_hash
                    })
                elif metadata.get('dish_id'):
                    seen_ids.add(metadata['dish_id'])
                
                # Проверка на дубли по названию
                if metadata.get('dish_name') and metadata['dish_name'] in seen_names:
                    duplicates.append({
                        "file": file_path,
                        "type": "duplicate_name", 
                        "dish_name": metadata['dish_name'],
                        "content_hash": content_hash
                    })
                elif metadata.get('dish_name'):
                    seen_names.add(metadata['dish_name'])
                
                # Валидация структуры TTK
                validation_result = self._validate_ttk_structure(file_content, file_path)
                if not validation_result['valid']:
                    invalid.append({
                        "file": file_path,
                        "issues": validation_result['issues'],
                        "content_hash": content_hash
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to analyze TTK file {file_path}: {e}")
                invalid.append({
                    "file": file_path,
                    "issues": [f"Analysis failed: {str(e)}"],
                    "content_hash": "unknown"
                })
        
        return {
            "duplicates": duplicates,
            "invalid": invalid,
            "hashes": hashes
        }
    
    def _extract_ttk_metadata(self, file_content: bytes, file_path: str) -> Dict[str, Any]:
        """Извлечение метаданных из TTK файла"""
        try:
            # Попытка парсинга XLSX для извлечения названия блюда и ID
            # Упрощенная реализация - можно расширить
            
            # Попробуем найти patterns в имени файла
            filename = Path(file_path).stem
            
            # Извлекаем ID из имени файла или контента
            dish_id_match = re.search(r'(?:id[_\-]?)(\w+)', filename, re.IGNORECASE)
            dish_id = dish_id_match.group(1) if dish_id_match else None
            
            # Извлекаем название блюда (очищенное)
            clean_name = re.sub(r'[_\-]?(ttk|id\w*)', '', filename, flags=re.IGNORECASE)
            clean_name = re.sub(r'[_\-]+', ' ', clean_name).strip()
            
            return {
                "dish_id": dish_id,
                "dish_name": clean_name if clean_name else filename,
                "file_size": len(file_content),
                "file_path": file_path
            }
            
        except Exception as e:
            logger.debug(f"Metadata extraction failed for {file_path}: {e}")
            return {
                "dish_name": Path(file_path).stem,
                "file_size": len(file_content),
                "file_path": file_path
            }
    
    def _validate_ttk_structure(self, file_content: bytes, file_path: str) -> Dict[str, Any]:
        """Валидация структуры TTK файла"""
        issues = []
        
        # Базовая валидация файла
        if len(file_content) < 1024:  # Слишком маленький файл
            issues.append("File too small to be valid XLSX")
        
        # Проверка что это валидный XLSX
        if not file_content.startswith(b'PK'):  # ZIP signature
            issues.append("Not a valid XLSX file (missing ZIP signature)")
        
        # Проверка размера файла (слишком большие файлы подозрительны)
        if len(file_content) > 50 * 1024 * 1024:  # 50MB
            issues.append("File too large (>50MB)")
        
        # Дополнительные проверки можно добавить здесь
        # Например, парсинг XLSX и проверка наличия обязательных листов
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _check_required_components(self, file_list: List[str]) -> List[str]:
        """Проверка наличия обязательных компонентов"""
        missing = []
        
        # iiko_TTK.xlsx всегда обязателен
        if "iiko_TTK.xlsx" not in file_list:
            missing.append("iiko_TTK.xlsx")
        
        # Остальные компоненты проверяются контекстно
        # (например, Dish-Skeletons.xlsx нужен только если есть missing dishes)
        
        return missing
    
    def _generate_cleanup_actions(self, result: ArchiveAnalysisResult) -> List[str]:
        """Генерация списка действий для очистки"""
        actions = []
        
        if result.duplicate_ttks:
            actions.append(f"Remove {len(result.duplicate_ttks)} duplicate TTK files")
            
        if result.invalid_ttks:
            actions.append(f"Remove {len(result.invalid_ttks)} invalid TTK files")
            
        if result.superfluous_files:
            actions.append(f"Remove {len(result.superfluous_files)} superfluous files")
            
        if result.missing_components:
            actions.append(f"Add missing components: {', '.join(result.missing_components)}")
            
        return actions
    
    def cleanup_archive(self, zip_buffer: io.BytesIO, 
                       analysis_result: Optional[ArchiveAnalysisResult] = None,
                       context: str = "unknown") -> Tuple[io.BytesIO, Dict[str, Any]]:
        """
        Автоматическая очистка архива
        
        Args:
            zip_buffer: Исходный ZIP архив
            analysis_result: Результат анализа (если уже выполнен)
            context: Контекст операции
            
        Returns:
            Tuple[очищенный_архив, статистика_очистки]
        """
        
        if analysis_result is None:
            analysis_result = self.analyze_archive(zip_buffer, context)
        
        if not analysis_result.has_issues():
            logger.info(f"Archive ({context}) is clean, no cleanup needed")
            return zip_buffer, {"cleaned": False, "issues_found": False}
        
        logger.info(f"Starting cleanup of archive ({context}): {analysis_result.get_summary()}")
        
        # Создаем новый чистый архив
        clean_buffer = io.BytesIO()
        cleanup_stats = {
            "cleaned": True,
            "original_files": 0,
            "removed_files": 0,
            "final_files": 0,
            "removed_duplicates": len(analysis_result.duplicate_ttks),
            "removed_invalid": len(analysis_result.invalid_ttks),
            "removed_superfluous": len(analysis_result.superfluous_files)
        }
        
        # Множества файлов для удаления
        files_to_remove = set()
        files_to_remove.update(f["file"] for f in analysis_result.duplicate_ttks)
        files_to_remove.update(f["file"] for f in analysis_result.invalid_ttks)
        files_to_remove.update(analysis_result.superfluous_files)
        
        try:
            with zipfile.ZipFile(zip_buffer, 'r') as source_zf:
                with zipfile.ZipFile(clean_buffer, 'w', zipfile.ZIP_DEFLATED) as target_zf:
                    
                    cleanup_stats["original_files"] = len(source_zf.namelist())
                    
                    for file_info in source_zf.infolist():
                        if file_info.filename not in files_to_remove:
                            # Копируем чистый файл
                            file_content = source_zf.read(file_info.filename)
                            target_zf.writestr(file_info, file_content)
                        else:
                            cleanup_stats["removed_files"] += 1
                            logger.info(f"Removed file: {file_info.filename}")
                    
                    cleanup_stats["final_files"] = len(target_zf.namelist())
            
            # Обновляем общую статистику
            self.cleanup_stats["total_processed"] += 1
            self.cleanup_stats["duplicates_removed"] += cleanup_stats["removed_duplicates"]
            self.cleanup_stats["invalid_removed"] += cleanup_stats["removed_invalid"]
            self.cleanup_stats["superfluous_removed"] += cleanup_stats["removed_superfluous"]
            if cleanup_stats["removed_files"] > 0:
                self.cleanup_stats["archives_cleaned"] += 1
            
            logger.info(f"Cleanup complete ({context}): {cleanup_stats}")
            
            clean_buffer.seek(0)
            return clean_buffer, cleanup_stats
            
        except Exception as e:
            logger.error(f"Archive cleanup failed ({context}): {e}")
            raise TTKValidationError(f"Cleanup failed: {str(e)}")
    
    def validate_single_ttk(self, ttk_content: bytes, filename: str = "unknown") -> Dict[str, Any]:
        """
        Валидация единичного TTK файла (для ALT XLSX экспорта)
        
        Returns:
            Dict с результатами валидации
        """
        try:
            metadata = self._extract_ttk_metadata(ttk_content, filename)
            structure_validation = self._validate_ttk_structure(ttk_content, filename)
            
            return {
                "valid": structure_validation["valid"],
                "metadata": metadata,
                "issues": structure_validation["issues"],
                "content_hash": hashlib.md5(ttk_content).hexdigest(),
                "file_size": len(ttk_content)
            }
            
        except Exception as e:
            logger.error(f"TTK validation failed for {filename}: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "metadata": {},
                "content_hash": "unknown",
                "file_size": len(ttk_content) if ttk_content else 0
            }
    
    def get_cleanup_statistics(self) -> Dict[str, Any]:
        """Получить статистику очистки"""
        return {
            **self.cleanup_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_statistics(self):
        """Сброс статистики"""
        self.cleanup_stats = {
            "total_processed": 0,
            "duplicates_removed": 0,
            "invalid_removed": 0,
            "superfluous_removed": 0,
            "archives_cleaned": 0
        }
    
    # Admin функция для отдельного анализа
    def admin_audit_archives(self, archives_dir: str = None) -> Dict[str, Any]:
        """
        Admin функция для полного аудита архивов
        Может использоваться для периодической проверки и отчетности
        """
        audit_result = {
            "timestamp": datetime.now().isoformat(),
            "archives_analyzed": 0,
            "total_issues": 0,
            "issues_by_type": {
                "duplicates": 0,
                "invalid": 0,
                "superfluous": 0,
                "missing_components": 0
            },
            "recommendations": []
        }
        
        # Реализация аудита файлов из директории (если нужно)
        # Пока возвращаем текущую статистику
        audit_result.update(self.get_cleanup_statistics())
        
        return audit_result


# Singleton instance для использования в приложении
alt_export_validator = ALTExportValidator()


def get_alt_export_validator() -> ALTExportValidator:
    """Получить экземпляр ALT Export Validator"""
    return alt_export_validator