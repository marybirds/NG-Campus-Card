<?php

use App\Http\Controllers\ProfileController;
use App\Http\Controllers\Auth\ExternalLoginController;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Cache;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

Route::get('/', function () {
    return view('welcome');
});

Route::get('/dashboard', function () {
    return view('dashboard');
})->middleware(['auth', 'verified'])->name('dashboard');

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');
});

use App\Http\Controllers\SmartcardController;

// Smartcard authentication routes (outside auth middleware)
Route::post('/smartcard/callback', [SmartcardController::class, 'callback'])->name('smartcard.callback');
Route::get('/smartcard/check', [SmartcardController::class, 'check'])->name('smartcard.check');


Route::post('/smartcard/store-token', function (Request $request) {
    try {
        $token = $request->input('token');
        $path = 'C:\Users\Madjid\NG-Campus-Card\smartcard_token.txt';

        file_put_contents($path, $token);
        Log::info("Token written to: $path");

        return response()->json(['status' => 'ok']);
    } catch (\Exception $e) {
        Log::error("Route error: " . $e->getMessage());
        return response()->json(['error' => $e->getMessage()], 500);
    }
});
#Route::get('/check-login', function () {
#if (Cache::has('external_login')) {
#return response()->json([
#'ready' => true,
#'email' => Cache::get('external_login')['email'],
#'password' => Cache::get('external_login')['password'],
#]);
#}

#return response()->json(['ready' => false]);
#});
#Route::post('/external-login', [ExternalLoginController::class, 'store']);

require __DIR__ . '/auth.php';
