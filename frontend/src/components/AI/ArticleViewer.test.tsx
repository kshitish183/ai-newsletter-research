import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ArticleViewer from './ArticleViewer';
import * as articleReader from '../Common/articleReader';

jest.mock('../Common/articleReader');

describe('ArticleViewer Component', () => {
  const mockAskQuestion = articleReader.askQuestion as jest.MockedFunction<typeof articleReader.askQuestion>;

  const mockArticleData = {
    url: 'https://example.com/test-article',
    title: 'Understanding AI RAG Pipelines',
    summary: 'RAG pipelines enhance large language models by retrieving relevant document passages.',
    main_idea: 'RAG provides grounded, cited answers without fine-tuning.',
    key_insights: ['Vector stores index chunks.', 'Embeddings measure semantic similarity.'],
    important_concepts: ['Retrieval', 'Embeddings', 'ChromaDB'],
    practical_takeaways: ['Store articles once.', 'Return citations with answers.']
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders article title, summary, main idea, and key insights', () => {
    render(<ArticleViewer articleData={mockArticleData} />);

    expect(screen.getByText('Understanding AI RAG Pipelines')).toBeInTheDocument();
    expect(screen.getByText(/RAG provides grounded, cited answers/i)).toBeInTheDocument();
    expect(screen.getByText('Vector stores index chunks.')).toBeInTheDocument();
  });

  test('submits question and renders answer with source citations', async () => {
    mockAskQuestion.mockResolvedValueOnce({
      answer: 'RAG combines search retrieval with neural text generation.',
      citations: [
        {
          text: 'RAG pipelines enhance large language models by retrieving relevant document passages.',
          chunk_index: 0,
          score: 0.92,
          url: 'https://example.com/test-article'
        }
      ]
    });

    render(<ArticleViewer articleData={mockArticleData} />);

    const input = screen.getByPlaceholderText(/ask about this article/i);
    const submitBtn = screen.getByRole('button', { name: /^ask$/i });

    fireEvent.change(input, { target: { value: 'What is RAG?' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockAskQuestion).toHaveBeenCalledWith('What is RAG?', {
        url: 'https://example.com/test-article',
        title: 'Understanding AI RAG Pipelines'
      });
      expect(screen.getByText('RAG combines search retrieval with neural text generation.')).toBeInTheDocument();
      expect(screen.getByText(/Source Citations \(1 retrieved\)/i)).toBeInTheDocument();
      expect(screen.getByText(/\[Chunk 1\]/i)).toBeInTheDocument();
    });
  });
});
