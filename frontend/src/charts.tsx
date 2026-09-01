import type { CSSProperties } from "react";
import type { BreachPatternsResponse } from "./api";

interface ChartsProps {
  patterns: BreachPatternsResponse | null;
}

export default function Charts({ patterns }: ChartsProps) {
  if (!patterns) {
    return (
      <section className="report-visuals" aria-labelledby="visuals-title">
        <div className="section-report-heading"><p className="eyebrow">INTELLIGENCE VISUALS</p><h2 id="visuals-title">Context requires a live intelligence engine.</h2></div>
        <div className="visual-unavailable-grid">
          <UnavailableVisual title="Market impact trajectory" detail="The documented analysis response provides summary metrics, not the time-series prices needed for a faithful line chart." />
          <UnavailableVisual title="Attack distribution" detail="The backend returns one company attack vector, not an attack-vector distribution." />
          <UnavailableVisual title="Industry & historical context" detail="Aggregate breach-pattern data is unavailable while the intelligence engine is offline." />
        </div>
      </section>
    );
  }

  const sectors = Object.entries(patterns.by_sector)
    .sort(([, firstCount], [, secondCount]) => secondCount - firstCount)
    .slice(0, 6);
  const years = Object.entries(patterns.by_year)
    .sort(([firstYear], [secondYear]) => firstYear.localeCompare(secondYear))
    .slice(-8);
  const severities = Object.entries(patterns.by_severity)
    .sort(([, firstCount], [, secondCount]) => secondCount - firstCount);
  const sectorMaximum = Math.max(...sectors.map(([, count]) => count), 1);
  const yearMaximum = Math.max(...years.map(([, count]) => count), 1);
  const severityTotal = severities.reduce((total, [, count]) => total + count, 0) || 1;
  const severitySegments = severities.reduce(
    (composition, [, count], index) => {
      const percentage = (count / severityTotal) * 100;
      const colors = ["#ff6a1a", "#ef9f35", "#d9b15b", "#d6d1c5", "#6b6861"];
      return {
        completedPercentage: composition.completedPercentage + percentage,
        segments: [...composition.segments, `${colors[index % colors.length]} ${composition.completedPercentage}% ${composition.completedPercentage + percentage}%`],
      };
    },
    { completedPercentage: 0, segments: [] as string[] },
  ).segments;

  return (
    <section className="report-visuals" aria-labelledby="visuals-title">
      <div className="section-report-heading"><p className="eyebrow">INTELLIGENCE VISUALS</p><h2 id="visuals-title">Portfolio context around this incident.</h2><span>BASED ON {patterns.total_breaches.toLocaleString("en-US")} DOCUMENTED BREACHES</span></div>
      <div className="visual-unavailable-grid">
        <UnavailableVisual title="Market impact trajectory" detail="The backend provides percentage changes and recovery data, but does not expose the underlying price series for a line chart." />
        <UnavailableVisual title="Attack distribution" detail="The backend does not expose an attack-vector aggregate. The company-specific vector appears in the incident overview." />
      </div>
      <div className="visual-grid">
        <article className="visual-card severity-visual">
          <div className="visual-heading"><div><p className="eyebrow">SEVERITY COMPOSITION</p><h3>Historical incident mix</h3></div><span>ALL RECORDS</span></div>
          <div className="severity-content">
            <div className="severity-donut" aria-label="Severity composition" style={{ "--severity-segments": `conic-gradient(${severitySegments.join(", ")})` } as CSSProperties}><span>{patterns.total_breaches.toLocaleString("en-US")}<small>BREACHES</small></span></div>
            <div className="severity-legend">{severities.map(([label, count], index) => <div key={label}><i style={{ background: ["#ff6a1a", "#ef9f35", "#d9b15b", "#d6d1c5", "#6b6861"][index % 5] }} /><span>{label}</span><b>{count}</b></div>)}</div>
          </div>
        </article>

        <article className="visual-card sector-visual">
          <div className="visual-heading"><div><p className="eyebrow">INDUSTRY COMPARISON</p><h3>Breach volume by sector</h3></div><span>COUNT</span></div>
          <div className="sector-bars">{sectors.map(([sector, count]) => <div className="sector-bar" key={sector} title={`${sector}: ${count} breaches`}><span>{sector}</span><div><i style={{ width: `${(count / sectorMaximum) * 100}%` }} /></div><b>{count}</b></div>)}</div>
        </article>

        <article className="visual-card trend-visual">
          <div className="visual-heading"><div><p className="eyebrow">HISTORICAL ACTIVITY</p><h3>Breaches by year</h3></div><span>COUNT</span></div>
          <div className="year-bars" aria-label="Historical breach activity by year">{years.map(([year, count]) => <div title={`${year}: ${count} breaches`} key={year}><i style={{ height: `${Math.max((count / yearMaximum) * 100, 6)}%` }} /><span>{year}</span></div>)}</div>
        </article>

        <article className="visual-card heatmap-visual">
          <div className="visual-heading"><div><p className="eyebrow">SECTOR ACTIVITY MAP</p><h3>Concentration by sector</h3></div><span>COUNT</span></div>
          <div className="sector-heatmap">{sectors.map(([sector, count]) => <div key={sector} title={`${sector}: ${count} breaches`} style={{ "--heat": `${Math.max(count / sectorMaximum, .14)}` } as CSSProperties}><span>{sector}</span><b>{count}</b></div>)}</div>
        </article>
      </div>
    </section>
  );
}

function UnavailableVisual({ title, detail }: { title: string; detail: string }) {
  return <article className="visual-unavailable"><span>DATA NOT EXPOSED</span><h3>{title}</h3><p>{detail}</p></article>;
}
