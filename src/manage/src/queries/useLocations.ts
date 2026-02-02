import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { axiosInstance } from './axiosInstance';
import { ApiResponse } from './api-response';
import { logExceptionError } from '../utils/errorLogger';

// Define the schema for location data
const locationSchema = z.object({
  _id: z.string(), // Accept any string ID format (ObjectId or custom string)
  isMobile: z.boolean().optional().default(false), // Make optional with default
  locationSlug: z.string(),
  name: z.string(),
  restaurantId: z.string().optional(), // Add restaurantId field
  isActive: z.boolean().optional(), // Add isActive field
  isOpen: z.boolean().optional(), // Add isOpen field
  alertNumbers: z.array(z.any()).optional(),
  address: z.string().or(z.object({}).passthrough()).optional(), // Accept string or object
  contact: z
    .object({
      email: z.string().optional(),
    })
    .optional(),
  workingHours: z
    .array(
      z.object({
        day: z.string(),
        isOpen: z.boolean(),
        startTime: z.string().optional().nullable(),
        endTime: z.string().optional().nullable(),
      }),
    )
    .optional(),
  timezone: z.string().optional(),
});

// Response schema for API validation
const locationsResponseSchema = z.object({
  data: z.array(locationSchema),
});

// TypeScript type for Location
export type Location = z.infer<typeof locationSchema>;

export function useLocations(restaurantId: string) {
  return useQuery<Location[]>({
    queryKey: ['locations', restaurantId],
    queryFn: async () => {
      if (!restaurantId) {
        throw new Error('Restaurant ID is required');
      }

      const response = await axiosInstance.get<ApiResponse<Location[]>>(
        `/restaurant/restaurants/${restaurantId}/locations`,
      );
      try {
        const validatedData = locationsResponseSchema.parse(response.data);
        return validatedData.data;
      } catch (error) {
        console.error('Location data validation failed:', error);
        // Log to Application Insights
        logExceptionError(new Error('Invalid location data format'), 'useLocations.validation', {
          restaurantId,
          zodError: error instanceof z.ZodError ? JSON.stringify(error.errors) : 'Unknown validation error',
          endpoint: `/restaurant/restaurants/${restaurantId}/locations`,
          responseData: JSON.stringify(response.data),
        });
        throw new Error('Invalid location data format');
      }
    },
    enabled: Boolean(restaurantId),
  });
}
