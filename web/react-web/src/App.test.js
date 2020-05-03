import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  const { getByText } = render(<App />);
  const linkElement = getByText(/April 13 predictions: Personal communication/i);
  expect(linkElement).toBeInTheDocument();
});
