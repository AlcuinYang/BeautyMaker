import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

type ScoreRadarChartProps = {
  data: Array<{ metric: string; score: number }>;
};

export function ScoreRadarChart({ data }: ScoreRadarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-xs text-slate-500">
        暂无评分数据
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data}>
        <PolarGrid stroke="rgba(226, 232, 240, 0.25)" />
        <PolarAngleAxis dataKey="metric" tick={{ fill: "#cbd5f5", fontSize: 12 }} />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 10]}
          tick={{ fill: "#64748b", fontSize: 10 }}
          stroke="rgba(148, 163, 184, 0.3)"
        />
        <Radar
          name="评分"
          dataKey="score"
          stroke="#34d399"
          strokeWidth={2}
          fill="#34d399"
          fillOpacity={0.25}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
