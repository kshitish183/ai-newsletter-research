import axios from "axios";

const getApiBaseUrl = (): string => {
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }
  if (
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1")
  ) {
    return "http://localhost:8000";
  }
  return "https://ai-newsletter-research.onrender.com";
};

const API_BASE_URL = getApiBaseUrl();

export async function fetchArticle(url: string) {
  try {
    const response = await axios.post(`${API_BASE_URL}/documents/analyze`, { url });
    console.log("Fetched article data:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching article:", error);
    throw error;
  }
}

export interface Citation {
  text: string;
  chunk_index: number;
  score: number;
  url?: string;
}

export interface QAResponseData {
  answer: string;
  citations: Citation[];
}

export async function askQuestion(
  question: string,
  articleContext?: { url?: string; title?: string }
): Promise<QAResponseData> {
  try {
    const response = await axios.post<QAResponseData>(`${API_BASE_URL}/documents/ask`, {
      question,
      url: articleContext?.url,
      title: articleContext?.title,
    });
    const data = response.data;
    if (typeof data.answer !== "string") {
      throw new Error("The article Q&A response did not contain a text answer.");
    }
    return {
      answer: data.answer,
      citations: Array.isArray(data.citations) ? data.citations : []
    };
  } catch (error) {
    console.error("Error asking question:", error);
    throw error;
  }
}