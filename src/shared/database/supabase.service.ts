import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Injectable()
export class SupabaseService implements OnModuleInit {
  private supabaseClient: SupabaseClient;

  constructor(private readonly configService: ConfigService) {}

  onModuleInit(): void {
    const url = this.configService.get<string>('supabase.url');
    const serviceKey = this.configService.get<string>('supabase.serviceKey');

    if (!url) {
      throw new Error(
        'SUPABASE_URL is not configured. Set the SUPABASE_URL environment variable.',
      );
    }

    if (!serviceKey) {
      throw new Error(
        'SUPABASE_SERVICE_KEY is not configured. Set the SUPABASE_SERVICE_KEY environment variable.',
      );
    }

    this.supabaseClient = createClient(url, serviceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });
  }

  get db(): SupabaseClient {
    if (!this.supabaseClient) {
      throw new Error('SupabaseService not yet initialized. Was onModuleInit called?');
    }
    return this.supabaseClient;
  }
}
