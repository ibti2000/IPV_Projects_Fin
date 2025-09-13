import numpy as np
from scipy.stats import norm

def blackscholes(S, K, T, r, sigma, option_type = "call"):
    #S = Spot Price, K = Strike Price, T = Maturity, r = risk free rate
    #sigma = standard deviation (volatility) option type impacts formula call or put

    d1 = (np.log(S/K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    #calculate option price now
    #d1: Standardized measure of how far the (forward-looking) stock price is above strike, adjusted for volatility. 
    #d2 same as d1 but shift down - gives actual prop of excercise

    if option_type.lower() == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
    elif option_type.lower() == "put":
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
    else:
        raise ValueError("Option must be either 'call' or 'put'")

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)

    return price, delta, gamma, vega 


