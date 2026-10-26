import { render, screen } from '@testing-library/react';
import App from './App';

test('renders top bar with Jobs and Resumes', () => {
  render(<App />);
  expect(screen.getAllByText('Jobs').length).toBeGreaterThan(0);
  expect(screen.getByText('Resumes')).toBeInTheDocument();
});
