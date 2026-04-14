import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { EventEmitterModule } from '@nestjs/event-emitter';
import { ScheduleModule } from '@nestjs/schedule';
import { BullModule } from '@nestjs/bullmq';

import configuration from '@config/configuration';
import { DatabaseModule } from '@shared/database/database.module';

import { PropertiesModule } from '@modules/properties/properties.module';
import { ReservationsModule } from '@modules/reservations/reservations.module';
import { GuestsModule } from '@modules/guests/guests.module';
import { ChannelManagerModule } from '@modules/channel-manager/channel-manager.module';
import { OwnerAlertsModule } from '@modules/owner-alerts/owner-alerts.module';
import { MessagingModule } from '@modules/messaging/messaging.module';
import { FinancialsModule } from '@modules/financials/financials.module';
import { CleaningModule } from '@modules/cleaning/cleaning.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
    }),
    EventEmitterModule.forRoot(),
    ScheduleModule.forRoot(),
    BullModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        connection: {
          host: config.get('redis.host'),
          port: config.get<number>('redis.port'),
          password: config.get('redis.password') || undefined,
        },
      }),
      inject: [ConfigService],
    }),
    DatabaseModule,
    PropertiesModule,
    ReservationsModule,
    GuestsModule,
    ChannelManagerModule,
    OwnerAlertsModule,
    MessagingModule,
    FinancialsModule,
    CleaningModule,
  ],
  controllers: [],
  providers: [],
})
export class AppModule {}
