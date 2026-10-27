import { render, screen } from '@testing-library/react';
import App from './App';

test('renders top bar with Application, Find Match and Profile', () => {
  render(<App />);
  expect(screen.getAllByText('Find Match').length).toBeGreaterThan(0);
  expect(screen.getByText('Resumes')).toBeInTheDocument();
});
