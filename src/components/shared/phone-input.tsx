'use client';

import { cn } from "@/lib/utils";
import PhoneInput, { Country, formatPhoneNumber as formatPhoneNumberIntl } from 'react-phone-number-input';
import { isValidPhoneNumber } from 'react-phone-number-input';
import 'react-phone-number-input/style.css';
import { CheckCircle2, XCircle } from "lucide-react";

// Define the countries we want to allow
const allowedCountries: Country[] = ['CA','GB', 'US'];

interface PhoneNumberInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
  className?: string;
}

export function PhoneNumberInput({ 
  value, 
  onChange, 
  disabled, 
  error,
  className 
}: PhoneNumberInputProps) {
  const isValid = value ? isValidPhoneNumber(value) : undefined;
  const formattedNumber = value ? formatPhoneNumberIntl(value) : '';

  return (
    <div className="space-y-2">
      <div className={cn("relative", className)}>
        <PhoneInput
          international
          defaultCountry="GB"
          countries={allowedCountries}
          value={value}
          onChange={(newValue) => onChange(newValue || '')}
          disabled={disabled}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
            "file:border-0 file:bg-transparent file:text-sm file:font-medium",
            "placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-destructive focus-visible:ring-destructive",
            isValid === false && "border-destructive",
            isValid === true && "border-green-500",
            className
          )}
        />
        {value && (
          <div className="absolute right-3 top-2.5">
            {isValid ? (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-destructive" />
            )}
          </div>
        )}
      </div>
      {value && (
        <div className="text-sm">
          {isValid ? (
            <p className="text-green-600 flex items-center gap-1">
              <CheckCircle2 className="h-4 w-4" />
              Valid {formattedNumber}
            </p>
          ) : (
            <p className="text-destructive flex items-center gap-1">
              <XCircle className="h-4 w-4" />
              Please enter a valid UK or US phone number
            </p>
          )}
        </div>
      )}
    </div>
  );
} 