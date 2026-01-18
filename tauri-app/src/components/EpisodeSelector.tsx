interface EpisodeSelectorProps {
  totalEpisodes: number;
  selectedEpisodes: Set<number>;
  onToggle: (episode: number) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  disabled?: boolean;
}

export function EpisodeSelector({
  totalEpisodes,
  selectedEpisodes,
  onToggle,
  onSelectAll,
  onDeselectAll,
  disabled,
}: EpisodeSelectorProps) {
  const episodes = Array.from({ length: totalEpisodes }, (_, i) => i + 1);

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-300">
          Episodes ({selectedEpisodes.size}/{totalEpisodes})
        </h3>
        <div className="flex gap-2">
          <button
            onClick={onSelectAll}
            disabled={disabled}
            className="px-3 py-1 text-xs font-medium text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors disabled:opacity-50"
          >
            Select All
          </button>
          <button
            onClick={onDeselectAll}
            disabled={disabled}
            className="px-3 py-1 text-xs font-medium text-slate-400 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Deselect All
          </button>
        </div>
      </div>

      <div className="max-h-40 overflow-y-auto pr-2">
        <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 gap-2">
          {episodes.map((ep) => (
            <button
              key={ep}
              onClick={() => onToggle(ep)}
              disabled={disabled}
              className={`
                px-2 py-1.5 text-xs font-medium rounded-lg transition-all
                ${
                  selectedEpisodes.has(ep)
                    ? "bg-violet-600 text-white shadow-lg shadow-violet-500/20"
                    : "bg-slate-700/50 text-slate-400 hover:bg-slate-700"
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {ep}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
