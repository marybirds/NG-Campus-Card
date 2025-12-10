<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;

class ExternalLoginController extends Controller
{
    public function store(Request $request)
    {
        // data sent from Python
        $email = $request->input('email');
        $password = $request->input('password');

        Cache::put('external_login', compact('email', 'password'), 60);

        return response()->json(['status' => 'waiting']);
    }
}


