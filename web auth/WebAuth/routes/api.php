<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Auth\ExternalLoginController;


Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});

#Route::post('/external-login', [ExternalLoginController::class, 'store']);
