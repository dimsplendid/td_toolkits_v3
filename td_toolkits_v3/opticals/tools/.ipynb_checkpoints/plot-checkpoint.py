import matplotlib.pyplot as plt
import numpy as np

def tex_scientific(number, precise=2):
    result = f'{number:.{precise}e}'.split('e')
    if int(result[1]) == 0:
        return result[0]
    else:
        result = result[0] + '\\times 10^{' + str(int(result[1])) + '}'
        return result
    
def tex_math_str(coef, var, precise=2, scientific=False):
    if len(coef) != (len(var) + 1):
        print('coeff should have one more feature than var')
        return 'error len'
    if scientific == True:
        result = '$' + tex_scientific(coef[0], precise)
        for i in range(len(var)):
            item = tex_scientific(coef[i+1], precise) + var[i]
            if coef[1+i] < 0:
                result += item
            else:
                result += (' + ' + item)
    else:
        result = '$' + str(np.round(coef[0],precise))
        for i in range(len(var)):
            if np.round(coef[1+i],precise) == 0:
                continue
            item = str(np.round(coef[1+i],precise)) + var[i]
            if coef[1+i] < 0:
                result += item
            else:
                result += (' + ' + item)
    result += '$'
    return result

def aux_plot(data, LC, xyz, model, var_names, precise=2, scientific=False):
    xlabel = xyz[0]
    ylabel = xyz[1]
    zlabel = xyz[2]
    coeff = model.steps[2][1].coef_
    X = data[[xlabel, ylabel]].to_numpy()
    y = data[zlabel].to_numpy()
    R2_score = model.score(X,y)
    plt.figure(figsize=(10,8))
    ax = plt.axes(projection="3d")
    ax.scatter(data[xlabel], data[ylabel], data[zlabel], label='data')
    # fitting
    x_range = np.linspace(data[xlabel].min(), data[xlabel].max(), 50)
    y_range = np.linspace(data[ylabel].min(), data[ylabel].max(), 50)
    x_range, y_range = np.meshgrid(x_range, y_range)
    predict_region = np.array(list(zip(x_range.flatten(), y_range.flatten())))
    z_predict = model.predict(predict_region)
    ax.scatter(x_range, y_range, z_predict, label="fitting surface", alpha=0.1)
    formula = tex_math_str(coeff, var_names, precise, scientific)
    plt.title(LC + f"\n${zlabel}=$".replace('%', '\%') + formula + f"\n$R^2={R2_score:.2f}$", loc='left')
    plt.legend()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    file_name = f'img/{LC}_{zlabel}({xlabel}, {ylabel})_R2_{R2_score:.2f}.png'
    plt.savefig(file_name)