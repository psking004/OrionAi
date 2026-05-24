import React from "react";

export function HealthGauge({ score, size = 64, strokeWidth = 6 }: { score: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  let color = "hsl(var(--chart-4))"; // green
  if (score < 50) color = "hsl(var(--destructive))"; // red
  else if (score < 75) color = "hsl(var(--chart-1))"; // orange/amber
  else if (score < 90) color = "hsl(var(--chart-2))"; // yellow/teal

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }} data-testid={`health-gauge-${score}`}>
      <svg className="transform -rotate-90 w-full h-full">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="text-muted/30"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="font-mono font-bold text-sm tracking-tighter" style={{ color }}>{score}</span>
      </div>
    </div>
  );
}
