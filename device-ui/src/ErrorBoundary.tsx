import React from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="mx-auto max-w-xl p-8">
          <h1 className="text-xl font-semibold text-red-600">
            Something went wrong
          </h1>
          <p className="mt-2 text-gray-600">
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
          <button
            className="mt-4 rounded bg-black px-4 py-2 text-white"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
