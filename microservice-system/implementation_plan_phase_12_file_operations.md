# Phase 12: File Operations Library & Step Organization

**Status:** 📋 PLANNED  
**Estimated Timeline:** 4 Weeks  
**Stack:** Python FastAPI, Cross-platform libraries, PostgreSQL, React TypeScript

---

## 🎯 **PHASE OVERVIEW**

A comprehensive file operations library with 25+ operations (copy, move, download, create, edit, delete, compress, etc.) organized in a modular step library system. This will transform job step management with cross-platform file operations and extensible library architecture for custom step collections.

---

## 📁 **FILE OPERATIONS LIBRARY**

### **Core File Operations (25+ Operations)**

#### **Basic File Operations**
- **file.create**: Create new files with content
- **file.read**: Read file contents
- **file.write**: Write content to files
- **file.append**: Append content to existing files
- **file.copy**: Copy files locally or between systems
- **file.move**: Move/rename files
- **file.delete**: Delete files with confirmation
- **file.exists**: Check file existence

#### **Directory Operations**
- **dir.create**: Create directories recursively
- **dir.list**: List directory contents with filtering
- **dir.copy**: Copy directories recursively
- **dir.move**: Move directories
- **dir.delete**: Delete directories with contents
- **dir.sync**: Synchronize directories

#### **Advanced File Operations**
- **file.compress**: Create ZIP, TAR, GZIP archives
- **file.extract**: Extract archives
- **file.encrypt**: Encrypt files with various algorithms
- **file.decrypt**: Decrypt encrypted files
- **file.hash**: Calculate file hashes (MD5, SHA256, etc.)
- **file.compare**: Compare files for differences
- **file.search**: Search file contents with regex
- **file.replace**: Find and replace in files

#### **Network File Operations**
- **file.download**: Download files from URLs
- **file.upload**: Upload files to remote systems
- **file.ftp**: FTP file operations
- **file.sftp**: SFTP file operations
- **file.s3**: AWS S3 file operations
- **file.azure**: Azure Blob storage operations

#### **File Metadata Operations**
- **file.permissions**: Set file permissions
- **file.ownership**: Change file ownership
- **file.attributes**: Modify file attributes
- **file.timestamps**: Update file timestamps

---

## 📋 **IMPLEMENTATION PHASES**

### **PHASE 12.1: Step Library Framework** (Week 1)

#### **Step Library Architecture**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class StepDefinition:
    name: str
    category: str
    description: str
    parameters: Dict[str, Any]
    platform_support: List[str]  # ['windows', 'linux', 'macos']
    required_permissions: List[str]
    examples: List[Dict[str, Any]]

class StepLibrary(ABC):
    """Base class for step libraries"""
    
    @abstractmethod
    def get_library_info(self) -> Dict[str, Any]:
        """Return library metadata"""
        pass
    
    @abstractmethod
    def get_step_definitions(self) -> List[StepDefinition]:
        """Return all step definitions in this library"""
        pass
    
    @abstractmethod
    def execute_step(self, step_type: str, config: Dict, context: Any) -> Any:
        """Execute a step from this library"""
        pass

class FileOperationsLibrary(StepLibrary):
    def get_library_info(self) -> Dict[str, Any]:
        return {
            'name': 'File Operations',
            'version': '1.0.0',
            'description': 'Comprehensive file and directory operations',
            'author': 'OpsConductor Team',
            'categories': ['file', 'directory', 'archive', 'network']
        }
    
    def get_step_definitions(self) -> List[StepDefinition]:
        return [
            StepDefinition(
                name='file.create',
                category='file',
                description='Create a new file with specified content',
                parameters={
                    'path': {'type': 'string', 'required': True, 'description': 'File path'},
                    'content': {'type': 'string', 'required': False, 'description': 'File content'},
                    'encoding': {'type': 'string', 'default': 'utf-8', 'description': 'File encoding'},
                    'overwrite': {'type': 'boolean', 'default': False, 'description': 'Overwrite if exists'}
                },
                platform_support=['windows', 'linux', 'macos'],
                required_permissions=['write'],
                examples=[
                    {
                        'name': 'Create configuration file',
                        'config': {
                            'path': '/etc/myapp/config.json',
                            'content': '{"debug": true, "port": 8080}',
                            'overwrite': True
                        }
                    }
                ]
            ),
            # ... more step definitions
        ]
```

#### **Step Registry System**
```python
class StepRegistry:
    def __init__(self):
        self.libraries: Dict[str, StepLibrary] = {}
        self.step_cache: Dict[str, StepDefinition] = {}
    
    def register_library(self, library: StepLibrary):
        """Register a step library"""
        info = library.get_library_info()
        self.libraries[info['name']] = library
        
        # Cache step definitions
        for step_def in library.get_step_definitions():
            self.step_cache[step_def.name] = step_def
    
    def get_available_steps(self, category: str = None, platform: str = None) -> List[StepDefinition]:
        """Get available steps with optional filtering"""
        steps = list(self.step_cache.values())
        
        if category:
            steps = [s for s in steps if s.category == category]
        
        if platform:
            steps = [s for s in steps if platform in s.platform_support]
        
        return steps
    
    def execute_step(self, step_type: str, config: Dict, context: Any) -> Any:
        """Execute a step by delegating to appropriate library"""
        if step_type not in self.step_cache:
            raise ValueError(f"Unknown step type: {step_type}")
        
        # Find library that owns this step
        for library in self.libraries.values():
            step_names = [s.name for s in library.get_step_definitions()]
            if step_type in step_names:
                return library.execute_step(step_type, config, context)
        
        raise ValueError(f"No library found for step type: {step_type}")
```

#### **Database Schema for Step Libraries**
```sql
-- Step library metadata
CREATE TABLE step_libraries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    categories JSONB,
    is_enabled BOOLEAN DEFAULT true,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step definitions cache
CREATE TABLE step_definitions (
    id SERIAL PRIMARY KEY,
    library_id INTEGER REFERENCES step_libraries(id),
    step_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL,
    platform_support JSONB NOT NULL,
    required_permissions JSONB,
    examples JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(library_id, step_name)
);

-- Custom step collections
CREATE TABLE step_collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,  -- Array of step configurations
    created_by INTEGER REFERENCES users(id),
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **PHASE 12.2: Comprehensive File Operations Library** (Week 2)

#### **Cross-Platform File Operations**
```python
import os
import shutil
import zipfile
import tarfile
import hashlib
from pathlib import Path
from typing import Union, List, Dict, Any

class CrossPlatformFileOperations:
    @staticmethod
    def create_file(path: str, content: str = '', encoding: str = 'utf-8', overwrite: bool = False) -> Dict[str, Any]:
        """Create a file with specified content"""
        file_path = Path(path)
        
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File {path} already exists")
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            'path': str(file_path.absolute()),
            'size': file_path.stat().st_size,
            'created': True
        }
    
    @staticmethod
    def copy_file(source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
        """Copy file from source to destination"""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file {source} not found")
        
        if dst_path.exists() and not overwrite:
            raise FileExistsError(f"Destination {destination} already exists")
        
        # Create destination directory if needed
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(src_path, dst_path)
        
        return {
            'source': str(src_path.absolute()),
            'destination': str(dst_path.absolute()),
            'size': dst_path.stat().st_size,
            'copied': True
        }
    
    @staticmethod
    def compress_files(files: List[str], archive_path: str, format: str = 'zip') -> Dict[str, Any]:
        """Compress files into an archive"""
        archive_path_obj = Path(archive_path)
        archive_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'zip':
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    file_obj = Path(file_path)
                    if file_obj.exists():
                        zipf.write(file_obj, file_obj.name)
        
        elif format.lower() in ['tar', 'tar.gz', 'tgz']:
            mode = 'w:gz' if format.lower() in ['tar.gz', 'tgz'] else 'w'
            with tarfile.open(archive_path, mode) as tarf:
                for file_path in files:
                    file_obj = Path(file_path)
                    if file_obj.exists():
                        tarf.add(file_obj, file_obj.name)
        
        return {
            'archive_path': str(archive_path_obj.absolute()),
            'format': format,
            'files_count': len(files),
            'size': archive_path_obj.stat().st_size
        }
    
    @staticmethod
    def calculate_hash(file_path: str, algorithm: str = 'sha256') -> Dict[str, Any]:
        """Calculate file hash"""
        hash_obj = hashlib.new(algorithm.lower())
        file_obj = Path(file_path)
        
        if not file_obj.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        with open(file_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return {
            'file_path': str(file_obj.absolute()),
            'algorithm': algorithm.upper(),
            'hash': hash_obj.hexdigest(),
            'size': file_obj.stat().st_size
        }
```

#### **Network File Operations**
```python
import aiohttp
import asyncio
from urllib.parse import urlparse

class NetworkFileOperations:
    @staticmethod
    async def download_file(url: str, destination: str, chunk_size: int = 8192) -> Dict[str, Any]:
        """Download file from URL"""
        dst_path = Path(destination)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(dst_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                
                return {
                    'url': url,
                    'destination': str(dst_path.absolute()),
                    'size': downloaded,
                    'total_size': total_size,
                    'downloaded': True
                }
    
    @staticmethod
    async def upload_file_http(file_path: str, upload_url: str, field_name: str = 'file') -> Dict[str, Any]:
        """Upload file via HTTP POST"""
        file_obj = Path(file_path)
        
        if not file_obj.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        data = aiohttp.FormData()
        data.add_field(field_name, open(file_obj, 'rb'), filename=file_obj.name)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(upload_url, data=data) as response:
                response.raise_for_status()
                
                return {
                    'file_path': str(file_obj.absolute()),
                    'upload_url': upload_url,
                    'size': file_obj.stat().st_size,
                    'response_status': response.status,
                    'uploaded': True
                }
```

---

### **PHASE 12.3: Cross-Platform Execution Engine** (Week 3)

#### **Platform-Specific Implementations**
```python
class WindowsFileOperations(CrossPlatformFileOperations):
    @staticmethod
    def set_file_attributes(file_path: str, attributes: Dict[str, bool]) -> Dict[str, Any]:
        """Set Windows file attributes"""
        import win32api
        import win32con
        
        file_obj = Path(file_path)
        if not file_obj.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        current_attrs = win32api.GetFileAttributes(str(file_obj))
        new_attrs = current_attrs
        
        if attributes.get('hidden'):
            new_attrs |= win32con.FILE_ATTRIBUTE_HIDDEN
        else:
            new_attrs &= ~win32con.FILE_ATTRIBUTE_HIDDEN
        
        if attributes.get('readonly'):
            new_attrs |= win32con.FILE_ATTRIBUTE_READONLY
        else:
            new_attrs &= ~win32con.FILE_ATTRIBUTE_READONLY
        
        win32api.SetFileAttributes(str(file_obj), new_attrs)
        
        return {
            'file_path': str(file_obj.absolute()),
            'attributes_set': attributes,
            'success': True
        }

class LinuxFileOperations(CrossPlatformFileOperations):
    @staticmethod
    def set_file_permissions(file_path: str, mode: str) -> Dict[str, Any]:
        """Set Unix file permissions"""
        file_obj = Path(file_path)
        if not file_obj.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        # Convert octal string to integer
        octal_mode = int(mode, 8) if isinstance(mode, str) else mode
        
        os.chmod(file_obj, octal_mode)
        
        return {
            'file_path': str(file_obj.absolute()),
            'mode': oct(octal_mode),
            'success': True
        }
    
    @staticmethod
    def change_ownership(file_path: str, owner: str, group: str = None) -> Dict[str, Any]:
        """Change file ownership"""
        import pwd
        import grp
        
        file_obj = Path(file_path)
        if not file_obj.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        # Get UID and GID
        uid = pwd.getpwnam(owner).pw_uid
        gid = grp.getgrnam(group).gr_gid if group else -1
        
        os.chown(file_obj, uid, gid)
        
        return {
            'file_path': str(file_obj.absolute()),
            'owner': owner,
            'group': group,
            'success': True
        }
```

#### **Step Execution Engine**
```python
class FileOperationExecutor:
    def __init__(self):
        self.platform = self.detect_platform()
        self.operations = self.get_platform_operations()
    
    def detect_platform(self) -> str:
        """Detect current platform"""
        import platform
        system = platform.system().lower()
        
        if system == 'windows':
            return 'windows'
        elif system in ['linux', 'darwin']:
            return 'linux'  # Treat macOS as Linux for file operations
        else:
            return 'unknown'
    
    def get_platform_operations(self):
        """Get platform-specific operations"""
        if self.platform == 'windows':
            return WindowsFileOperations()
        else:
            return LinuxFileOperations()
    
    async def execute_file_operation(self, operation: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operation based on type"""
        operation_map = {
            'file.create': self.operations.create_file,
            'file.copy': self.operations.copy_file,
            'file.compress': self.operations.compress_files,
            'file.hash': self.operations.calculate_hash,
            'file.download': NetworkFileOperations.download_file,
            'file.upload': NetworkFileOperations.upload_file_http,
        }
        
        if operation not in operation_map:
            raise ValueError(f"Unknown file operation: {operation}")
        
        operation_func = operation_map[operation]
        
        # Execute operation (handle both sync and async functions)
        if asyncio.iscoroutinefunction(operation_func):
            return await operation_func(**config)
        else:
            return operation_func(**config)
```

---

### **PHASE 12.4: Frontend Integration & Library Management** (Week 4)

#### **Step Library Browser**
```typescript
const StepLibraryBrowser = () => {
  const [libraries, setLibraries] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredSteps = useMemo(() => {
    return libraries
      .flatMap(lib => lib.steps)
      .filter(step => {
        const matchesCategory = selectedCategory === 'all' || step.category === selectedCategory;
        const matchesSearch = step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             step.description.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesCategory && matchesSearch;
      });
  }, [libraries, selectedCategory, searchTerm]);
  
  return (
    <div className="step-library-browser">
      <div className="library-filters">
        <TextField
          placeholder="Search steps..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Select value={selectedCategory} onChange={setSelectedCategory}>
          <MenuItem value="all">All Categories</MenuItem>
          <MenuItem value="file">File Operations</MenuItem>
          <MenuItem value="directory">Directory Operations</MenuItem>
          <MenuItem value="archive">Archive Operations</MenuItem>
          <MenuItem value="network">Network Operations</MenuItem>
        </Select>
      </div>
      
      <div className="step-grid">
        {filteredSteps.map(step => (
          <StepCard
            key={step.name}
            step={step}
            onAddToJob={addStepToJob}
            onViewDetails={viewStepDetails}
          />
        ))}
      </div>
    </div>
  );
};
```

#### **File Operation Step Builder**
```typescript
const FileOperationStepBuilder = ({ step, onStepUpdate }) => {
  const [operation, setOperation] = useState(step.config.operation || '');
  const [parameters, setParameters] = useState(step.config.parameters || {});
  
  const operationDefinition = useStepDefinition(operation);
  
  return (
    <div className="file-operation-builder">
      <FormControl>
        <InputLabel>File Operation</InputLabel>
        <Select value={operation} onChange={setOperation}>
          <MenuItem value="file.create">Create File</MenuItem>
          <MenuItem value="file.copy">Copy File</MenuItem>
          <MenuItem value="file.move">Move File</MenuItem>
          <MenuItem value="file.delete">Delete File</MenuItem>
          <MenuItem value="file.compress">Compress Files</MenuItem>
          <MenuItem value="file.download">Download File</MenuItem>
        </Select>
      </FormControl>
      
      {operationDefinition && (
        <DynamicParameterForm
          definition={operationDefinition}
          values={parameters}
          onChange={setParameters}
        />
      )}
      
      <StepPreview
        operation={operation}
        parameters={parameters}
      />
    </div>
  );
};
```

---

## 🔧 **API ENDPOINTS**

### **Step Library Management**
```
GET    /api/v1/step-libraries           # List available step libraries
GET    /api/v1/step-libraries/:id       # Get library details
POST   /api/v1/step-libraries           # Install new library
DELETE /api/v1/step-libraries/:id       # Uninstall library
```

### **Step Definitions**
```
GET    /api/v1/steps                    # List available steps
GET    /api/v1/steps/:name              # Get step definition
GET    /api/v1/steps/categories         # List step categories
POST   /api/v1/steps/:name/validate     # Validate step configuration
```

### **Step Collections**
```
POST   /api/v1/step-collections         # Create step collection
GET    /api/v1/step-collections         # List step collections
GET    /api/v1/step-collections/:id     # Get collection details
PUT    /api/v1/step-collections/:id     # Update collection
DELETE /api/v1/step-collections/:id     # Delete collection
```

---

## 🎯 **EXPECTED BENEFITS**

### **Operational Benefits**
- **Comprehensive File Management**: 25+ file operations covering all common needs
- **Cross-Platform Consistency**: Unified file operations across Windows, Linux, and macOS
- **Modular Architecture**: Extensible library system for custom operations
- **Reusable Components**: Step collections for common file operation patterns

### **Developer Experience**
- **Rich Step Library**: Extensive library of pre-built file operations
- **Easy Extension**: Simple framework for adding custom operations
- **Platform Abstraction**: Write once, run anywhere file operations
- **Template System**: Reusable step collections and templates

### **Enterprise Features**
- **Security**: Proper permission handling and validation
- **Audit Trail**: Complete tracking of all file operations
- **Error Handling**: Robust error handling and recovery
- **Performance**: Optimized for large file operations and bulk processing

---

This phase will establish OpsConductor as a comprehensive file management automation platform, providing enterprise-grade file operations with cross-platform support and extensible architecture for custom automation needs.