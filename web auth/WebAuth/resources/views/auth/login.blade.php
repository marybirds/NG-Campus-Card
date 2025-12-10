<x-guest-layout>
    <!-- Session Status -->
    <x-auth-session-status class="mb-4" :status="session('status')" />

    <form method="POST" action="{{ route('login') }}">
        @csrf

        <!-- Email Address -->
        <div>
            <x-input-label for="email" :value="__('Email')" />
            <x-text-input id="email" class="block mt-1 w-full" type="email" name="email" :value="old('email')" required autofocus autocomplete="username" />
            <x-input-error :messages="$errors->get('email')" class="mt-2" />
        </div>

        <!-- Password -->
        <div class="mt-4">
            <x-input-label for="password" :value="__('Password')" />

            <x-text-input id="password" class="block mt-1 w-full"
                            type="password"
                            name="password"
                            required autocomplete="current-password" />

            <x-input-error :messages="$errors->get('password')" class="mt-2" />
        </div>

        <!-- Remember Me -->
        <div class="block mt-4">
            <label for="remember_me" class="inline-flex items-center">
                <input id="remember_me" type="checkbox" class="rounded dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-indigo-600 shadow-sm focus:ring-indigo-500 dark:focus:ring-indigo-600 dark:focus:ring-offset-gray-800" name="remember">
                <span class="ms-2 text-sm text-gray-600 dark:text-gray-400">{{ __('Remember me') }}</span>
            </label>
        </div>

        <div class="flex items-center justify-end mt-4">
            @if (Route::has('password.request'))
                <a class="underline text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-gray-800" href="{{ route('password.request') }}">
                    {{ __('Forgot your password?') }}
                </a>
            @endif

            <x-primary-button class="ms-3">
                {{ __('Log in') }}
            </x-primary-button>
        </div>

        <!-- Smartcard Login Button -->
        <div class="mt-6 flex items-center justify-center">
            <button type="button"
                    id="smartcard-login-btn"
                    class="inline-flex items-center px-4 py-2 bg-gray-800 dark:bg-gray-200 border border-transparent rounded-md font-semibold text-xs text-white dark:text-gray-800 uppercase tracking-widest hover:bg-gray-700 dark:hover:bg-white focus:bg-gray-700 dark:focus:bg-white active:bg-gray-900 dark:active:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition ease-in-out duration-150">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                </svg>
                {{ __('Login with Smartcard') }}
            </button>
        </div>
        <div id="smartcard-token-display" class="mt-2 text-xs text-gray-500 text-center hidden"></div>
        <!-- Smartcard Status Message -->
        <div id="smartcard-status" class="mt-2 text-sm text-gray-600 dark:text-gray-400 text-center hidden">
            {{ __('Waiting for smartcard... Please insert your card.') }}
        </div>

    </form>

    @push('scripts')
<script>
document.addEventListener('DOMContentLoaded', function() {
    const smartcardBtn = document.getElementById('smartcard-login-btn');
    const smartcardStatus = document.getElementById('smartcard-status');
    const loginForm = document.querySelector('form[action="{{ route('login') }}"]');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const tokenDisplay = document.getElementById('smartcard-token-display');

    let isListening = false;
    let pollInterval = null;

    smartcardBtn.addEventListener('click', function() {
        if (isListening) {
            stopListening();
            return;
        }
        startListening();
    });

    function startListening() {
        isListening = true;
        smartcardBtn.textContent = 'Cancel Smartcard Login';
        smartcardBtn.classList.add('bg-red-600', 'hover:bg-red-700');
        smartcardBtn.classList.remove('bg-gray-800', 'hover:bg-gray-700');
        smartcardStatus.classList.remove('hidden');
        smartcardStatus.textContent = 'Waiting for smartcard... Please insert your card.';

        // Generate and display token
        const sessionToken = btoa(Math.random().toString(36).substring(2) + Date.now());
        localStorage.setItem('smartcard_session', sessionToken);

        fetch('/smartcard/store-token', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: sessionToken})
        })
        .then(response => response.json())
        .then(data => console.log('Token storage result:', data))
        .catch(error => console.error('Token storage failed:', error));

        tokenDisplay.textContent = 'Token: ' + sessionToken;
        tokenDisplay.classList.remove('hidden');
        console.log('Smartcard token:', sessionToken); // DEBUG

        // Start polling for credentials
        pollForCredentials(sessionToken);
    }

    function stopListening() {
        isListening = false;
        if (pollInterval) clearInterval(pollInterval);
        smartcardBtn.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
            </svg>
            Login with Smartcard
        `;
        smartcardBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
        smartcardBtn.classList.add('bg-gray-800', 'hover:bg-gray-700');
        smartcardStatus.classList.add('hidden');
        tokenDisplay.classList.add('hidden');
    }

    async function pollForCredentials(sessionToken) {
        pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/smartcard/check?token=' + sessionToken);
                const data = await response.json();
                console.log('Polling...', data); // DEBUG

                if (data.credentials) {
                    clearInterval(pollInterval);

                    // Fill form and submit
                    emailInput.value = data.credentials.email;
                    passwordInput.value = data.credentials.password;

                    smartcardStatus.textContent = 'Smartcard detected! Logging in...';
                    smartcardStatus.classList.remove('text-red-600');
                    smartcardStatus.classList.add('text-green-600');

                    // Give user feedback then submit
                    setTimeout(() => {
                        loginForm.submit();
                    }, 1000);
                }
            } catch (error) {
                console.error('Poll error:', error); // DEBUG
            }
        }, 2000); // Poll every 2 seconds
    }
});
</script>
@endpush

</x-guest-layout>
