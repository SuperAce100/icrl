"use client";

interface SuccessMessageProps {
  message: string;
  onReset: () => void;
}

export function SuccessMessage({ message, onReset }: SuccessMessageProps) {
  return (
    <div className="text-center space-y-6 py-8">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-900/50 text-emerald-400">
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
      
      <div>
        <h3 className="text-xl font-semibold text-white mb-2">Feedback Recorded!</h3>
        <p className="text-gray-400">{message}</p>
      </div>

      <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 max-w-md mx-auto">
        <p className="text-sm text-gray-300">
          Your preference has been added to the database. Future answers will be influenced by
          examples like this one, making the system better over time.
        </p>
      </div>

      <button
        onClick={onReset}
        className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors"
      >
        Ask Another Question
      </button>
    </div>
  );
}
