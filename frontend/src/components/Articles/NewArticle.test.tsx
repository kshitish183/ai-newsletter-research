import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NewArticle from './NewArticle';
import * as articleReader from '../Common/articleReader';

jest.mock('../Common/articleReader');

describe('NewArticle Component', () => {
  const mockFetchArticle = articleReader.fetchArticle as jest.MockedFunction<typeof articleReader.fetchArticle>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders URL input field and submit button', () => {
    render(<NewArticle />);
    expect(screen.getByPlaceholderText(/https:\/\/example.com\/article/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /open in reader/i })).toBeInTheDocument();
  });

  test('handles successful article fetch', async () => {
    const onOpenMock = jest.fn();
    mockFetchArticle.mockResolvedValueOnce({
      title: 'Test Article',
      summary: 'Test Summary'
    });

    render(<NewArticle onOpen={onOpenMock} />);

    const input = screen.getByPlaceholderText(/https:\/\/example.com\/article/i);
    const button = screen.getByRole('button', { name: /open in reader/i });

    fireEvent.change(input, { target: { value: 'https://example.com/test' } });
    fireEvent.click(button);

    expect(screen.getByRole('button', { name: /opening\.\.\./i })).toBeInTheDocument();

    await waitFor(() => {
      expect(mockFetchArticle).toHaveBeenCalledWith('https://example.com/test');
      expect(onOpenMock).toHaveBeenCalledWith('https://example.com/test', expect.anything());
    });
  });

  test('displays error message on fetch failure', async () => {
    mockFetchArticle.mockRejectedValueOnce({
      response: { data: { detail: 'Domain resolves to a private IP address.' } }
    });

    render(<NewArticle />);

    const input = screen.getByPlaceholderText(/https:\/\/example.com\/article/i);
    const button = screen.getByRole('button', { name: /open in reader/i });

    fireEvent.change(input, { target: { value: 'http://127.0.0.1/private' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Domain resolves to a private IP address.');
    });
  });
});
