export interface DatasetUploadResponse {
  id: string;
  file_name: string;
  file_type: string;
  file_title: string;
  description: string;
  row_count: number;
  columns: string[];
  file_version: number;
  created_at: string;
  updated_at: string;
}
