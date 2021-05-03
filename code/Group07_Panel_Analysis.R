# install.packages('dplyr',repos = "http://cran.us.r-project.org") 
# install.packages('tidyr',repos = "http://cran.us.r-project.org")
# install.packages('RColorBrewer',repos = "http://cran.us.r-project.org")
# install.packages('ggplot2',repos = "http://cran.us.r-project.org")
# install.packages('knitr',repos = "http://cran.us.r-project.org")
# install.packages('png',repos = "http://cran.us.r-project.org")

# install.packages('animation',repos = "http://cran.us.r-project.org")
# install.packages('gifski',repos = "http://cran.us.r-project.org")
# install.packages('table1',repos = "http://cran.us.r-project.org")
# install.packages('gtsummary',repos = "http://cran.us.r-project.org")
# install.packages('gt',repos = "http://cran.us.r-project.org")
# install.packages('corrplot',repos = "http://cran.us.r-project.org")
# install.packages('xtable',repos = "http://cran.us.r-project.org")
# install.packages('car',repos = "http://cran.us.r-project.org")
# install.packages('DT',repos = "http://cran.us.r-project.org")

# install.packages('AER',repos = "http://cran.us.r-project.org")    
# install.packages('plm',repos = "http://cran.us.r-project.org")   
# install.packages('stargazer',repos = "http://cran.us.r-project.org") 
# install.packages('lattice',repos = "http://cran.us.r-project.org")

# library(dplyr) 
# library(tidyr)
# library(RColorBrewer)
# library(ggplot2)
# library(knitr)
# library(png)

# library(table1)
# library(gtsummary)
# library(gt)
# library(corrplot)
# library(xtable)
# library(car)
# library(DT)

# library(AER)   
library(plm)
library(lattice)


### Reading Panel Dataset
data <- read.csv("airbnb_data/Mar2019_Feb2020_Airbnb_panel_2.csv")

# We check check the whether the data is balanced or not.
is.data.frame(data)
# check the dimension of data
dim(data)
# check if the panel data is balanced or not using `plm` package function
is.pbalanced(data)

pdata <- pdata.frame(data, index = c("listing_id", "last_scraped"))
pdata = pdata[!duplicated(pdata), ]


# removing the columns with factors less than 2
(l <- sapply(pdata, function(x) is.factor(x)))
m <- pdata[, l]
ifelse(n <- sapply(m, function(x) length(levels(x))) == 1, "DROP", "NODROP")


### Performing panel analysis with all three models
# First Difference model
fd = plm(price ~ experience + host_is_superhost + security_deposit + cleaning_fee +
         availability_30 + number_of_reviews + reviews_per_month + 
         review_scores_rating + total_rainfall + mean_temp + mean_humidity + 
         ConsumerPrices + Nominal_GDP_YOY + ExchangeRate + StraitTimesIndex + 
         UnemploymentRate +  sentiment_score , data = pdata, 
         index = c("listing_id", "last_scraped"), 
                  model = "fd") 
summary(fd)

# Fixed Effect model    
fe = plm(price ~ experience + host_is_superhost + security_deposit + cleaning_fee +
         availability_30 + number_of_reviews + reviews_per_month + 
         review_scores_rating + total_rainfall + mean_temp + mean_humidity + 
         ConsumerPrices + Nominal_GDP_YOY + ExchangeRate + StraitTimesIndex + 
         UnemploymentRate +  sentiment_score, data = pdata, 
         index = c("listing_id", "last_scraped"), 
                  model = "within", effect = "twoways") 
                   
summary(fe)
plmtest(fe, effect="twoways", type="ghm")

# Random Effect model
re = plm(price ~ experience + host_is_superhost + security_deposit + cleaning_fee +
         availability_30 + number_of_reviews + reviews_per_month + 
         review_scores_rating + total_rainfall + mean_temp + mean_humidity + 
         ConsumerPrices + Nominal_GDP_YOY + ExchangeRate + StraitTimesIndex + 
         UnemploymentRate +  sentiment_score, data = pdata, 
         index = c("listing_id", "last_scraped"), 
                  model = "random") 

summary(re)

## PHTest for checking which model to select First Effect or Random Effect
phtest(fe, re)