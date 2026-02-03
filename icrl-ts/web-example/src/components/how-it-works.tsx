"use client";

const steps = [
  { number: 1, label: "Enter a prompt", colorClass: "bg-primary/10 text-primary" },
  { number: 2, label: "Retrieve examples", colorClass: "bg-icrl-blue/10 text-icrl-blue" },
  { number: 3, label: "Generate options", colorClass: "bg-icrl-yellow/30 text-icrl-stone-dark" },
  { number: 4, label: "Choose the best", colorClass: "bg-primary/10 text-primary" },
  { number: 5, label: "Store & learn", colorClass: "bg-icrl-blue/10 text-icrl-blue" },
];

export function HowItWorks() {
  return (
    <div className="bg-card rounded-xl p-6 border shadow-sm">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        How it works
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {steps.map((step) => (
          <div key={step.number} className="flex flex-col items-center text-center p-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold mb-2 ${step.colorClass}`}
            >
              {step.number}
            </div>
            <p className="text-sm">{step.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
