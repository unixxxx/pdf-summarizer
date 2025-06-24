/**
 * Upload configuration
 */
export const uploadConfig = {
  /**
   * File size threshold for multipart upload (in bytes)
   * Files larger than this will use multipart upload
   */
  multipartThreshold: 100 * 1024 * 1024, // 100MB

  /**
   * Part size for multipart uploads (in bytes)
   */
  multipartPartSize: 5 * 1024 * 1024, // 5MB

  /**
   * Maximum file size allowed (in bytes)
   */
  maxFileSize: 500 * 1024 * 1024, // 500MB

  /**
   * Allowed file types
   */
  allowedFileTypes: [
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ],
};
