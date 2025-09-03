import React, { useState } from 'react';
import LibraryManager from './LibraryManager';
import { BookOpen, Package, Settings, Cog, Trash2 } from 'lucide-react';

const StepLibrarySettings: React.FC = () => {
  const [showLibraryManager, setShowLibraryManager] = useState(false);

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center gap-2">
              <BookOpen size={20} /> Step Library Management
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Install, manage, and configure job step libraries for the system.
            </p>
          </div>
          <button
            onClick={() => setShowLibraryManager(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Settings size={16} className="mr-2" />
            Manage Libraries
          </button>
        </div>

        <div className="mt-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Package size={16} className="text-blue-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">Install Libraries</p>
                  <p className="text-sm text-gray-500">Add new step libraries</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <Cog size={16} className="text-green-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">Configure Libraries</p>
                  <p className="text-sm text-gray-500">Enable/disable libraries</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                    <Trash2 size={16} className="text-red-600" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">Remove Libraries</p>
                  <p className="text-sm text-gray-500">Uninstall unused libraries</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                About Step Libraries
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  Step libraries contain reusable job steps that can be used across different jobs. 
                  Libraries can be installed from ZIP files and may require license keys for premium features.
                  Managing libraries here affects all users and job creation workflows.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Library Manager Modal */}
      {showLibraryManager && (
        <LibraryManager onClose={() => setShowLibraryManager(false)} />
      )}
    </div>
  );
};

export default StepLibrarySettings;