import { render } from '@testing-library/react';
import App from './App';

test('renders the InsightAI dashboard', () => {
  const { getByText } = render(<App />);

  expect(getByText(/good evening, kshitish/i)).toBeInTheDocument();
});
