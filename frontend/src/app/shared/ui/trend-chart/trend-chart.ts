import { Component, computed, input } from '@angular/core';
import { ScoreTrendPoint } from '../../models/dashboard.models';

interface ChartCoord {
  x: number;
  y: number;
  label: string;
  score: number;
}

interface ChartData {
  coords: ChartCoord[];
  polylinePoints: string;
  areaPath: string;
  yLabels: { y: number; label: number }[];
  pad: { top: number; right: number; bottom: number; left: number };
  chartH: number;
  isSinglePoint: boolean;
}

@Component({
  selector: 'app-trend-chart',
  standalone: true,
  templateUrl: './trend-chart.html',
  styleUrl: './trend-chart.css',
})
export class TrendChartComponent {
  readonly points = input<ScoreTrendPoint[]>([]);
  readonly width = input<number>(600);
  readonly height = input<number>(200);
  readonly minScore = input<number>(60);
  readonly maxScore = input<number>(100);

  protected readonly gradientId = `trend-gradient-${Math.random().toString(36).slice(2, 8)}`;

  protected readonly chartData = computed((): ChartData | null => {
    const pts = this.points();
    if (pts.length < 1) return null;

    const w = this.width();
    const h = this.height();
    const pad = { top: 16, right: 24, bottom: 32, left: 40 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;
    const minY = this.minScore();
    const maxY = this.maxScore();
    const isSinglePoint = pts.length === 1;

    const coords: ChartCoord[] = isSinglePoint
      ? [
          {
            x: pad.left + chartW / 2,
            y: pad.top + chartH - ((pts[0].score - minY) / (maxY - minY)) * chartH,
            label: pts[0].version,
            score: pts[0].score,
          },
        ]
      : pts.map((pt, i) => ({
          x: pad.left + (i * chartW) / (pts.length - 1),
          y: pad.top + chartH - ((pt.score - minY) / (maxY - minY)) * chartH,
          label: pt.version,
          score: pt.score,
        }));

    const polylinePoints = coords.map((c) => `${c.x},${c.y}`).join(' ');
    const areaPath = [
      `M${coords[0].x},${pad.top + chartH}`,
      ...coords.map((c) => `L${c.x},${c.y}`),
      `L${coords[coords.length - 1].x},${pad.top + chartH}`,
      'Z',
    ].join(' ');

    const step = (maxY - minY) / 4;
    const yLabels = [0, 1, 2, 3, 4].map((i) => {
      const val = minY + step * i;
      return {
        y: pad.top + chartH - ((val - minY) / (maxY - minY)) * chartH,
        label: Math.round(val),
      };
    });

    return { coords, polylinePoints, areaPath, yLabels, pad, chartH, isSinglePoint };
  });
}
