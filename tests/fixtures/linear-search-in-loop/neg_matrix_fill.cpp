void fillMatrix(int g[10][10], int n) {
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            g[i][j] = i * j;
        }
    }
}
