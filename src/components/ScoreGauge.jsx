export default function ScoreGauge({ score, maxScore = 900, risk = 'Medium' }) {
  const progress = Math.max(0, Math.min(100, (score / maxScore) * 100))
  const tone = risk.toLowerCase()

  return (
    <div
      className={`score-gauge score-gauge-${tone}`}
      style={{ '--score-progress': `${progress}%` }}
      role="img"
      aria-label={`Credit score ${score} out of ${maxScore}, ${risk} risk`}
    >
      <div className="score-gauge-inner">
        <span className="score-label">YOUR SCORE</span>
        <strong>{score}</strong>
        <span className="score-outof">out of {maxScore}</span>
      </div>
    </div>
  )
}
