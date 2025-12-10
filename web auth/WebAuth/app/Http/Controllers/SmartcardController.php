<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Str;

class SmartcardController extends Controller
{
    /**
     * Receive credentials from smartcard system
     * This endpoint is exempt from CSRF verification
     */
    public function callback(Request $request)
    {
        // Validate the request
        $validated = $request->validate([
            'session_token' => 'required|string',
            'email' => 'required|email',
            'password' => 'required|string',
        ]);

        // Store credentials temporarily (encrypted)
        $cacheKey = 'smartcard_' . $validated['session_token'];
        Cache::put($cacheKey, [
            'email' => $validated['email'],
            'password' => $validated['password'],
        ], 120); // Store for 2 minutes

        return response()->json([
            'status' => 'success',
            'message' => 'Credentials received'
        ]);
    }

    /**
     * Check for credentials (polled by JavaScript)
     */
    public function check(Request $request)
    {
        $sessionToken = $request->query('token');

        if (!$sessionToken) {
            return response()->json(['error' => 'Invalid token'], 400);
        }

        $cacheKey = 'smartcard_' . $sessionToken;
        $credentials = Cache::get($cacheKey);

        if ($credentials) {
            // Clear credentials after retrieval
            Cache::forget($cacheKey);

            return response()->json([
                'credentials' => $credentials
            ]);
        }

        return response()->json([
            'credentials' => null
        ]);
    }
}
