import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

type ScoreRadarChartProps = {
  data: Array<{ key: string; label: string; score: number; comment?: string }>;
  compositeScore?: number | null;
};

export function ScoreRadarChart({ data, compositeScore }: ScoreRadarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-xs text-slate-500">
        暂无评分数据
      </div>
    );
  }

  const renderAngleTick = (props: any) => {
    const { x, y, payload, textAnchor } = props;
    const node = data[payload.index];
    const scoreText = node ? node.score.toFixed(1) : "";
    return (
      <text x={x} y={y} textAnchor={textAnchor} fill="#cbd5f5" fontSize={12}>
        <tspan>{payload.value}</tspan>
        <tspan x={x} dy={14} fill="#94a3b8">
          {scoreText}
        </tspan>
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data} margin={{ top: 12, right: 12, bottom: 12, left: 12 }}>
        <PolarGrid stroke="rgba(226, 232, 240, 0.15)" />
        <PolarAngleAxis dataKey="label" tick={renderAngleTick} />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 10]}
          tick={{ fill: "#64748b", fontSize: 10 }}
          tickCount={3}
          stroke="rgba(148, 163, 184, 0.15)"
        />
        <Radar
          name="评分"
          dataKey="score"
          stroke="url(#radarStroke)"
          strokeWidth={2.5}
          fill="url(#radarFill)"
          fillOpacity={0.35}
        />
        {typeof compositeScore === "number" && (
          <>
            <defs>
              <radialGradient id="centerPulse" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#34d399" stopOpacity={0.25} />
                <stop offset="100%" stopColor="transparent" stopOpacity={0} />
              </radialGradient>
            </defs>
            <circle cx="50%" cy="50%" r="16" fill="url(#centerPulse)" />
            <text x="50%" y="50%" textAnchor="middle" fill="#a7f3d0" fontSize={20} fontWeight={700}>
              {(compositeScore * 10).toFixed(1)}
            </text>
            <text x="50%" y="50%" dy={18} textAnchor="middle" fill="#cbd5f5" fontSize={10}>
              综合
            </text>
          </>
        )}
        <defs>
          <linearGradient id="radarStroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#34d399" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity={0.9} />
          </linearGradient>
          <linearGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#34d399" stopOpacity={0.25} />
          </linearGradient>
        </defs>
      </RadarChart>
    </ResponsiveContainer>
  );
}
