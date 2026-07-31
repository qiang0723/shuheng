import Link from "next/link";
import { percent, signedPercent } from "../../lib/format";
import type { Experiment } from "../../lib/types";

export function CalibrationStrip({ experiments }: { experiments: Experiment[] }) {
  return (
    <div className="calibration-list">
      {experiments.map((experiment) => {
        const metric = experiment.metrics!;
        return (
          <Link href={`/experiments/${experiment.id}`} className="calibration-row" key={experiment.id}>
            <span className="calibration-order">{metric.order}</span>
            <span className="calibration-name"><strong>{experiment.name}</strong><small>事件 {experiment.id}</small></span>
            <span className="calibration-prediction">密封{metric.predictedDirection === "positive" ? "正" : "负"}·{percent(metric.confidence, 0)}</span>
            <span className={metric.directionHit ? "hit yes" : "hit no"}>{metric.directionHit ? "方向命中" : "方向未中"}</span>
            <span className="calibration-return">{signedPercent(metric.caar, 2)}</span>
          </Link>
        );
      })}
    </div>
  );
}
