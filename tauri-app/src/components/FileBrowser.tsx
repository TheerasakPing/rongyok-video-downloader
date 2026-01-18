import { useState } from "react";
import {
  FolderOpen,
  Film,
  Trash2,
  Play,
  FileVideo,
  HardDrive,
  RefreshCw,
} from "lucide-react";
import { Button } from "./Button";

interface FileInfo {
  name: string;
  path: string;
  size: number;
  isEpisode: boolean;
  isMerged: boolean;
}

interface FileBrowserProps {
  outputDir: string;
  files: FileInfo[];
  onRefresh: () => void;
  onOpenFolder: () => void;
  onDelete: (paths: string[]) => void;
  onPlay: (path: string) => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function FileBrowser({
  outputDir,
  files,
  onRefresh,
  onOpenFolder,
  onDelete,
  onPlay,
}: FileBrowserProps) {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

  const totalSize = files.reduce((sum, f) => sum + f.size, 0);
  const episodeFiles = files.filter((f) => f.isEpisode);
  const mergedFiles = files.filter((f) => f.isMerged);

  const toggleSelect = (path: string) => {
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedFiles(new Set(files.map((f) => f.path)));
  };

  const deselectAll = () => {
    setSelectedFiles(new Set());
  };

  const deleteSelected = () => {
    if (selectedFiles.size > 0) {
      onDelete(Array.from(selectedFiles));
      setSelectedFiles(new Set());
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            <FolderOpen size={16} />
            {outputDir}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {files.length} files • {formatBytes(totalSize)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            leftIcon={<RefreshCw size={14} />}
            onClick={onRefresh}
          >
            Refresh
          </Button>
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<FolderOpen size={14} />}
            onClick={onOpenFolder}
          >
            Open Folder
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Film size={14} />
            Episodes
          </div>
          <div className="text-lg font-bold text-white">
            {episodeFiles.length}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <FileVideo size={14} />
            Merged
          </div>
          <div className="text-lg font-bold text-white">
            {mergedFiles.length}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <HardDrive size={14} />
            Total Size
          </div>
          <div className="text-lg font-bold text-white">
            {formatBytes(totalSize)}
          </div>
        </div>
      </div>

      {/* Actions */}
      {files.length > 0 && (
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={selectAll}>
            Select All
          </Button>
          <Button size="sm" variant="ghost" onClick={deselectAll}>
            Deselect
          </Button>
          {selectedFiles.size > 0 && (
            <Button
              size="sm"
              variant="danger"
              leftIcon={<Trash2 size={14} />}
              onClick={deleteSelected}
            >
              Delete ({selectedFiles.size})
            </Button>
          )}
        </div>
      )}

      {/* File List */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        {files.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No files in output directory
          </div>
        ) : (
          <div className="max-h-64 overflow-y-auto divide-y divide-slate-700/50">
            {files.map((file) => (
              <div
                key={file.path}
                className={`flex items-center gap-3 px-4 py-2 hover:bg-slate-700/30 transition-colors cursor-pointer ${
                  selectedFiles.has(file.path) ? "bg-violet-600/20" : ""
                }`}
                onClick={() => toggleSelect(file.path)}
              >
                <input
                  type="checkbox"
                  checked={selectedFiles.has(file.path)}
                  onChange={() => {}}
                  className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-violet-600"
                />
                <div
                  className={`p-1.5 rounded ${
                    file.isMerged
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "bg-violet-500/20 text-violet-400"
                  }`}
                >
                  <FileVideo size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{file.name}</div>
                  <div className="text-xs text-slate-500">
                    {formatBytes(file.size)}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onPlay(file.path);
                  }}
                  className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <Play size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
