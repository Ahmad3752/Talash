

const GRADE_COLORS = {
  A: 'bg-brand-teal/20 text-brand-teal border-brand-teal',
  B: 'bg-brand-green/20 text-brand-green border-brand-green',
  C: 'bg-brand-amber/20 text-brand-amber border-brand-amber',
  D: 'bg-brand-orange/20 text-brand-orange border-brand-orange',
  F: 'bg-brand-rose/20 text-brand-rose border-brand-rose',
};

const GradeBadge = ({ grade }) => {
  const normalizedGrade = (grade || 'F').charAt(0).toUpperCase();
  const colorClass = GRADE_COLORS[normalizedGrade] || GRADE_COLORS.F;

  return (
    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-full border text-xs font-bold font-mono ${colorClass}`}>
      {normalizedGrade}
    </span>
  );
};

export default GradeBadge;
