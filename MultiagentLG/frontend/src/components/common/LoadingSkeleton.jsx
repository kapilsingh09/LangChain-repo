import React from "react";

export const LoadingSkeleton = ({ lines = 6, className = "" }) => {
  return (
    <div className={`space-y-4 w-full animate-pulse ${className}`}>
      <div className="h-8 bg-neutral-800/60 rounded-lg w-3/4 border border-white/5" />
      <div className="h-4 bg-neutral-800/40 rounded w-1/3 border border-white/5" />
      
      <div className="pt-4 space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-4 bg-neutral-800/30 rounded border border-white/5"
            style={{
              width: `${Math.max(45, 95 - (i % 4) * 15)}%`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default LoadingSkeleton;
