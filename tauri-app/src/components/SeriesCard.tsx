import { SeriesInfo } from "../types";
import { Film, Tv } from "lucide-react";

interface SeriesCardProps {
  series: SeriesInfo | null;
  isLoading?: boolean;
}

export function SeriesCard({ series, isLoading }: SeriesCardProps) {
  if (isLoading) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 animate-pulse">
        <div className="flex gap-4">
          <div className="w-24 h-32 bg-slate-700 rounded-lg" />
          <div className="flex-1 space-y-3">
            <div className="h-5 bg-slate-700 rounded w-3/4" />
            <div className="h-4 bg-slate-700 rounded w-1/2" />
          </div>
        </div>
      </div>
    );
  }

  if (!series) {
    return (
      <div className="bg-slate-800/30 rounded-xl p-8 border border-dashed border-slate-700 text-center">
        <Tv className="mx-auto text-slate-600 mb-3" size={48} />
        <p className="text-slate-500 text-sm">
          Enter a URL and click Fetch to load series information
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-xl p-4 border border-slate-700 shadow-xl">
      <div className="flex gap-4">
        {series.posterUrl ? (
          <img
            src={series.posterUrl}
            alt={series.title}
            className="w-24 h-32 object-cover rounded-lg shadow-lg"
          />
        ) : (
          <div className="w-24 h-32 bg-slate-700 rounded-lg flex items-center justify-center">
            <Film className="text-slate-500" size={32} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-white truncate mb-1">
            {series.title}
          </h2>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span className="px-2 py-0.5 bg-violet-500/20 text-violet-300 rounded-md">
              ID: {series.seriesId}
            </span>
            <span>•</span>
            <span>{series.totalEpisodes} Episodes</span>
          </div>
          <p className="mt-2 text-xs text-emerald-400">
            {Object.keys(series.episodeUrls).length} URLs cached
          </p>
        </div>
      </div>
    </div>
  );
}
