"""Companion Python code extracted from chapters/ch09_problem_set.tex.

Archived as supplementary material for the GitHub repository.
"""

# --- Snippet 1 ---
            from scipy.stats import norm
            def inverse_normal_cdf(u):
                return norm.ppf(u)
        

# --- Snippet 2 ---
        def geom_asian_option(optType, S_0, strike, expiry, r, sigma, npaths, nsteps):
            delta_t = expiry / nsteps
            N_rands = npaths * nsteps

            z_s = iter(np.random.normal(0, 1, N_rands)) # iter function to create an iterator
            V_T = 0
            for _ in range(npaths):
                S_t = S_0
                S_av = S_0
                for _ in range(nsteps):
                    z = next(z_s)
                    """
                    Your codes here, update S_t and S_av
                    """
                S_T = S_t # Final stock price
                S_av = S_av ** (1/(nsteps+1)) # Average stock price
                V_T += max( S_av - strike, 0.0) if optType==CALL else max( strike - S_av, 0.0)
                # print(f"{S_T}, {S_av}")
                
            """
            Your codes here, calculate the price of the option
            """
            return (V_0)
        

# --- Snippet 3 ---
        r_usd = 0.05
        r_eur = 0.03
        x_0 = 1.08
        expiries = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 12.0]
        fwd_prem_cents = [5.2716, 7.0007, 8.0169, 8.9944, 9.7660, 10.7318, 10.9863]
 
        # Cents need to be converted to dollars!!
        fwd_premium = [ fpc/100 for fpc in fwd_prem_cents]
        """
        Your codes here, calculate the strikes: strikes=[...]
        """
    

# --- Snippet 4 ---
        def black_formula(f, k, expiry, vol):
            """
            Your codes here, gain the d1 and d2 values
            """
            return f*norm.cdf(d1) - k*norm.cdf(d2)
    

# --- Snippet 5 ---
        def black_vega(f, k, expiry, vol):
            epsilon = 1e-4
            """
            Your codes here, gain the vega value by central finite difference
            """
            return vega
    

# --- Snippet 6 ---
        def implied_vol(prem, f, k, expiry, init_guess):
            max_iter = 10
            ivol = init_guess # initial guess of implied volatility
            error = black_formula(f, k, expiry, ivol) - prem  # ivol is the root of this function
            vega = black_vega(f, k, expiry, ivol)
        
            count = 0
            while ( abs(error) > 1e-6 and count < max_iter ):
                """
                Your codes here, Newton-Raphson update: ivol = ivol - error/vega, error = ..., vega = ...
                """
        
            if count == max_iter:
                raise ValueError('Exceeded max iterations')
            else:
                return ivol
    

# --- Snippet 7 ---
        trades = list(zip(expiries, strikes, fwd_premium))
        print(trades)
        

        ivols = [ implied_vol(fp, k, k, t, 0.1 ) for t, k, fp in list(trades) ]
        print(f'Implied vols are : {ivols}')

        outright_vols =  list( zip(expiries, ivols) )

        prev_t, prev_ivol = outright_vols[0]
        fwd_vols = []
        for i in range(1, len(outright_vols)):
            prev_t, prev_ivol = outright_vols[i-1] # previous implied vol
            curr_t, curr_ivol = outright_vols[i] # current implied vol
            try:
                """
                Your codes here, calculate the forward volatilities: fwd_vol = ...
                """
            except:
                fwd_vol = None
            fwd_vols.append(fwd_vol)
        print(f'Implied fwd vols are : {fwd_vols}')
    

