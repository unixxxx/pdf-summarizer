/**
 * Document search criteria for API requests
 */
export interface DocumentSearchCriteria {
  search?: string;
  folder_id?: string;
  unfiled?: boolean;
  limit?: number;
  offset?: number;
}
